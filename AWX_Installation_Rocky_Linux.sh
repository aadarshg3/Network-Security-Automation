#!/usr/bin/env bash
# AWX on K3s - single-node lab install for Rocky/RHEL 9
# Based on github.com/kurokobo/awx-on-k3s (pinned tag)
# Modes: precheck | install | postcheck | all
set -Eeuo pipefail

TS="$(date +%Y%m%d-%H%M%S)"
readonly TS
readonly LOG_FILE="/var/log/awx-install-${TS}.log"
readonly K3S_VERSION="v1.29.6+k3s2"
readonly REPO_URL="https://github.com/kurokobo/awx-on-k3s.git"
readonly REPO_TAG="2.19.1+20260320.1"
readonly REPO_DIR="/opt/awx-on-k3s"
readonly DATA_DIR="/data"
readonly CRED_FILE="/root/awx-credentials.txt"
readonly KUBECTL="/usr/local/bin/kubectl"
readonly MIN_CPU=4
readonly MIN_RAM_GB=8
readonly MIN_ROOT_FREE_GB=40
export KUBECONFIG="/etc/rancher/k3s/k3s.yaml"

MODE="precheck"
AWX_HOST="awx-01.lab.local"
WAIT_MIN=30
ASSUME_YES=0
FAILS=0
WARNS=0

usage() {
  cat <<EOF
Usage: sudo $0 --mode <precheck|install|postcheck|all> [options]

  --mode MODE       precheck (default, read-only) | install | postcheck | all
  --awx-host FQDN   AWX URL hostname and system hostname (default: ${AWX_HOST})
  --wait-min N      Max minutes to wait for AWX pods (default: ${WAIT_MIN})
  --yes             Skip interactive confirmations
  -h, --help        Show this help
EOF
}

log()  { printf '%s [%-5s] %s\n' "$(date '+%F %T')" "$1" "$2"; }
pass() { log PASS "$1"; }
info() { log INFO "$1"; }
warn() { log WARN "$1"; WARNS=$((WARNS + 1)); }
fail() { log FAIL "$1"; FAILS=$((FAILS + 1)); }
die()  { log ERROR "$1"; exit 1; }

trap 'log ERROR "Line ${LINENO}: command failed: ${BASH_COMMAND}"' ERR

confirm() {
  [[ ${ASSUME_YES} -eq 1 ]] && return 0
  local ans
  read -r -p "$1 [y/N]: " ans
  [[ ${ans} =~ ^[Yy]$ ]]
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode)     MODE="${2:-}"; shift 2 ;;
      --awx-host) AWX_HOST="${2:-}"; shift 2 ;;
      --wait-min) WAIT_MIN="${2:-}"; shift 2 ;;
      --yes)      ASSUME_YES=1; shift ;;
      -h|--help)  usage; exit 0 ;;
      *)          usage; die "Unknown argument: $1" ;;
    esac
  done
  [[ ${MODE} =~ ^(precheck|install|postcheck|all)$ ]] || die "Invalid --mode: ${MODE}"
  [[ ${AWX_HOST} =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]] \
    || die "--awx-host must be a lowercase FQDN (e.g. awx-01.lab.local)"
  [[ ${WAIT_MIN} =~ ^[0-9]+$ ]] || die "--wait-min must be a number"
}

node_ready() {
  local out
  out=$("${KUBECTL}" get nodes --no-headers 2>/dev/null || true)
  [[ ${out} == *" Ready "* ]]
}

primary_ip() { ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}'; }

# ---------------- PRECHECK ----------------
check_os() {
  # shellcheck disable=SC1091
  . /etc/os-release
  local major="${VERSION_ID%%.*}"
  if [[ ${ID} =~ ^(rocky|rhel|almalinux|centos)$ && ${major} == "9" ]]; then
    pass "OS: ${PRETTY_NAME}"
  else
    fail "OS ${PRETTY_NAME} not tested (need Rocky/RHEL 9)"
  fi
  [[ $(uname -m) == "x86_64" ]] && pass "Arch x86_64" || fail "Arch $(uname -m) not x86_64"
}

check_resources() {
  local cpu ram_gb root_free_gb
  cpu=$(nproc)
  ram_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
  root_free_gb=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
  (( cpu >= MIN_CPU )) && pass "CPU ${cpu}" || warn "CPU ${cpu} < recommended ${MIN_CPU}"
  (( ram_gb >= MIN_RAM_GB )) && pass "RAM ${ram_gb} GiB" || warn "RAM ${ram_gb} GiB < recommended ${MIN_RAM_GB}"
  (( root_free_gb >= MIN_ROOT_FREE_GB )) && pass "/ free ${root_free_gb} GiB" \
    || fail "/ free ${root_free_gb} GiB < ${MIN_ROOT_FREE_GB} GiB"
}

check_network() {
  local ip
  ip=$(primary_ip)
  [[ -n ${ip} ]] && pass "Primary IPv4 ${ip}" || fail "No default IPv4 route"
  if ip -4 addr show scope global | grep -q dynamic; then
    warn "IPv4 is DHCP - use a static IP or router DHCP reservation"
  else
    pass "IPv4 is static"
  fi
  [[ $(timedatectl show -p NTPSynchronized --value 2>/dev/null) == "yes" ]] \
    && pass "NTP synchronized" || warn "NTP not synchronized"
  info "SELinux: $(getenforce 2>/dev/null || echo unknown)"
  systemctl is-active --quiet firewalld && info "firewalld active (install will disable it, as K3s recommends)"

  local p
  for p in 80 443 6443; do
    if ss -ltnH "sport = :${p}" | grep -q .; then
      if systemctl is-active --quiet k3s; then
        info "Port ${p} in use by existing K3s (re-run)"
      else
        fail "Port ${p} already in use by another service"
      fi
    else
      pass "Port ${p} free"
    fi
  done
}

check_urls() {
  local urls=(
    https://get.k3s.io https://github.com https://rpm.rancher.io
    https://quay.io https://registry-1.docker.io https://ghcr.io
  )
  local u code
  for u in "${urls[@]}"; do
    code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "${u}" || true)
    [[ ${code} != "000" ]] && pass "Reachable ${u} (HTTP ${code})" || fail "Unreachable ${u}"
  done
}

check_existing() {
  if command -v k3s >/dev/null 2>&1; then
    info "K3s already installed: $(k3s --version | head -1)"
  else
    pass "K3s not installed (fresh)"
  fi
  [[ -f ${CRED_FILE} ]] && info "Existing ${CRED_FILE} found - passwords will be reused"
  return 0
}

run_precheck() {
  info "===== PRECHECK ====="
  check_os
  check_resources
  check_network
  check_urls
  check_existing
  info "Precheck result: ${FAILS} fail, ${WARNS} warn"
}

# ---------------- INSTALL ----------------
prepare_host() {
  local ip
  ip=$(primary_ip)
  info "Setting hostname ${AWX_HOST} and /etc/hosts entry for ${ip}"
  hostnamectl set-hostname "${AWX_HOST}"
  cp -p /etc/hosts "/etc/hosts.bak-${TS}"
  if ! grep -Eq "^[0-9.]+[[:space:]]+${AWX_HOST//./\\.}([[:space:]]|$)" /etc/hosts; then
    printf '%s %s %s\n' "${ip}" "${AWX_HOST}" "${AWX_HOST%%.*}" >> /etc/hosts
  fi

  info "Disabling firewalld and nm-cloud-setup (K3s recommendation)"
  systemctl disable --now firewalld 2>/dev/null || true
  systemctl disable --now nm-cloud-setup.service nm-cloud-setup.timer 2>/dev/null || true

  dnf -y install git curl openssl tar
}

install_k3s() {
  if command -v k3s >/dev/null 2>&1 && k3s --version | grep -qF "${K3S_VERSION}"; then
    info "K3s ${K3S_VERSION} already installed - skipping"
  else
    info "Installing K3s ${K3S_VERSION}"
    curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="${K3S_VERSION}" sh -s - --write-kubeconfig-mode 644
  fi
  systemctl is-active --quiet k3s || die "k3s service not active"

  info "Waiting for node Ready"
  local _
  for _ in $(seq 1 60); do
    node_ready && { pass "Node Ready"; return 0; }
    sleep 5
  done
  die "Node not Ready after 5 minutes (check: journalctl -u k3s)"
}

fetch_repo() {
  if [[ -d ${REPO_DIR}/.git ]]; then
    info "Repo exists at ${REPO_DIR}"
    git -C "${REPO_DIR}" fetch --tags --quiet
  else
    git clone --quiet "${REPO_URL}" "${REPO_DIR}"
  fi
  git -C "${REPO_DIR}" checkout --quiet "${REPO_TAG}"
  pass "Repo at tag ${REPO_TAG}"
}

deploy_operator() {
  info "Deploying AWX Operator"
  "${KUBECTL}" apply -k "${REPO_DIR}/operator"
  "${KUBECTL}" -n awx rollout status deployment/awx-operator-controller-manager --timeout=600s
  pass "AWX Operator running"
}

write_credentials() {
  if [[ -f ${CRED_FILE} ]]; then
    info "Reusing passwords from ${CRED_FILE}"
    return 0
  fi
  (
    umask 077
    cat > "${CRED_FILE}" <<EOF
AWX_URL=https://${AWX_HOST}/
AWX_ADMIN_USER=admin
AWX_ADMIN_PASSWORD=$(openssl rand -hex 12)
AWX_POSTGRES_PASSWORD=$(openssl rand -hex 16)
EOF
  )
  info "Credentials written: ${CRED_FILE} (600)"
}

cred() { awk -F= -v k="$1" '$1==k {sub(/^[^=]*=/, ""); print; exit}' "${CRED_FILE}"; }

build_manifests() {
  local base="${REPO_DIR}/base" admin_pw pg_pw
  admin_pw=$(cred AWX_ADMIN_PASSWORD)
  pg_pw=$(cred AWX_POSTGRES_PASSWORD)
  [[ -n ${admin_pw} && -n ${pg_pw} ]] || die "Passwords missing in ${CRED_FILE}"

  if [[ ! -f ${base}/tls.crt || ! -f ${base}/tls.key ]]; then
    info "Generating self-signed TLS cert for ${AWX_HOST}"
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
      -out "${base}/tls.crt" -keyout "${base}/tls.key" \
      -subj "/CN=${AWX_HOST}/O=${AWX_HOST}" -addext "subjectAltName = DNS:${AWX_HOST}"
    chmod 600 "${base}/tls.key"
  fi

  sed -i -E "s/^([[:space:]]*- hostname:).*/\1 ${AWX_HOST}/" "${base}/awx.yaml"
  grep -q "hostname: ${AWX_HOST}$" "${base}/awx.yaml" || die "Failed to set hostname in awx.yaml"

  (
    umask 077
    cat > "${base}/kustomization.yaml" <<EOF
---
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: awx

generatorOptions:
  disableNameSuffixHash: true

secretGenerator:
  - name: awx-secret-tls
    type: kubernetes.io/tls
    files:
      - tls.crt
      - tls.key

  - name: awx-postgres-configuration
    type: Opaque
    literals:
      - host=awx-postgres-15
      - port=5432
      - database=awx
      - username=awx
      - password=${pg_pw}
      - type=managed

  - name: awx-admin-password
    type: Opaque
    literals:
      - password=${admin_pw}

resources:
  - pv.yaml
  - pvc.yaml
  - awx.yaml
EOF
  )
  pass "Manifests prepared (hostname, TLS, secrets)"
}

prepare_storage() {
  mkdir -p "${DATA_DIR}/postgres-15" "${DATA_DIR}/projects"
  chown 1000:0 "${DATA_DIR}/projects"
  pass "Storage dirs ready under ${DATA_DIR}"
}

deploy_awx() {
  info "Deploying AWX (first run pulls images; can take 10-20 min)"
  "${KUBECTL}" apply -k "${REPO_DIR}/base"

  local deadline=$(( $(date +%s) + WAIT_MIN * 60 ))
  local d
  for d in awx-web awx-task; do
    until "${KUBECTL}" -n awx get deployment "${d}" >/dev/null 2>&1; do
      (( $(date +%s) < deadline )) || die "Timeout: deployment ${d} not created (check operator logs)"
      info "Waiting for operator to create ${d}..."
      sleep 20
    done
    local left=$(( deadline - $(date +%s) ))
    (( left > 0 )) || die "Timeout waiting for ${d}"
    "${KUBECTL}" -n awx rollout status "deployment/${d}" --timeout="${left}s"
    pass "Deployment ${d} available"
  done
}

run_install() {
  info "===== INSTALL ====="
  confirm "ESXi snapshot of this VM taken (rollback point)?" || die "Take a snapshot first"
  prepare_host
  install_k3s
  fetch_repo
  deploy_operator
  write_credentials
  build_manifests
  prepare_storage
  deploy_awx
}

# ---------------- POSTCHECK ----------------
run_postcheck() {
  info "===== POSTCHECK ====="
  FAILS=0; WARNS=0
  systemctl is-active --quiet k3s && pass "Service k3s active" || fail "Service k3s not active"
  node_ready && pass "Node Ready" || fail "Node not Ready"

  local pods bad
  pods=$("${KUBECTL}" -n awx get pods --no-headers 2>/dev/null || true)
  bad=$(awk '$3=="Completed"{next} $3!="Running"{print; next} {split($2,a,"/"); if (a[1]!=a[2]) print}' <<<"${pods}")
  if [[ -n ${pods} && -z ${bad} ]]; then
    pass "All pods in namespace awx Running and Ready"
  else
    fail "Pods not healthy:"; printf '%s\n' "${bad:-no pods found}"
  fi
  "${KUBECTL}" -n awx get awx,pods,ingress 2>/dev/null || true

  local code
  code=$(curl -sk -o /dev/null -m 20 -w '%{http_code}' \
    --resolve "${AWX_HOST}:443:127.0.0.1" "https://${AWX_HOST}/api/v2/ping/" || true)
  [[ ${code} == "200" ]] && pass "AWX API ping HTTP 200" || fail "AWX API ping HTTP ${code}"

  if [[ -f ${CRED_FILE} ]]; then
    info "URL:      https://${AWX_HOST}/"
    info "User:     admin"
    info "Password: sudo grep AWX_ADMIN_PASSWORD ${CRED_FILE}"
  fi
  info "On your laptop, add to hosts file: $(primary_ip) ${AWX_HOST}"
  info "Postcheck result: ${FAILS} fail, ${WARNS} warn"
}

main() {
  [[ ${EUID} -eq 0 ]] || { echo "Run as root: sudo $0 ..."; exit 1; }
  parse_args "$@"
  exec > >(tee -a "${LOG_FILE}") 2>&1
  info "Mode=${MODE} AWX_HOST=${AWX_HOST} Log=${LOG_FILE}"

  case "${MODE}" in
    precheck)
      run_precheck ;;
    install|all)
      run_precheck
      (( FAILS == 0 )) || die "Precheck failed (${FAILS}) - fix FAIL items before install"
      run_install
      [[ ${MODE} == "all" ]] && run_postcheck ;;
    postcheck)
      run_postcheck ;;
  esac

  (( FAILS == 0 )) || die "Completed with ${FAILS} failure(s). Log: ${LOG_FILE}"
  info "Completed OK. Log: ${LOG_FILE}"
}

main "$@"
