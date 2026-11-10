#!/usr/bin/env bash
# Red Hat AAP 2.6 containerized - single-node growth topology (bundle install) on RHEL 9.6+/10
# Run as the non-root installation user (with sudo rights), NOT as root.
# Modes: precheck | install | postcheck | all
set -Eeuo pipefail

TS="$(date +%Y%m%d-%H%M%S)"
readonly TS
readonly LOG_FILE="${HOME}/aap-install-${TS}.log"
readonly WORK_DIR="${HOME}/aap"
readonly INV_NAME="inventory-lab"
readonly CRED_FILE="${HOME}/aap-credentials.txt"
readonly MIN_CPU=4
readonly MIN_RAM_GB=15
readonly MIN_ROOT_FREE_GB=60
readonly MIN_VARTMP_FREE_GB=3

MODE="precheck"
BUNDLE=""
FQDN="$(hostname -f 2>/dev/null || hostname)"
ASSUME_YES=0
FAILS=0
WARNS=0
BECOME_ARGS=()

usage() {
  cat <<EOF
Usage: $0 --mode <precheck|install|postcheck|all> [options]   (run as non-root user, e.g. aad)

  --mode MODE      precheck (default, read-only) | install | postcheck | all
  --bundle FILE    Path to ansible-automation-platform-containerized-setup-bundle-*.tar.gz
                   (required for install/all; optional for precheck)
  --fqdn NAME      AAP hostname (default: ${FQDN})
  --yes            Skip interactive confirmations
  -h, --help       Show this help
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
      --mode)   MODE="${2:-}"; shift 2 ;;
      --bundle) BUNDLE="${2:-}"; shift 2 ;;
      --fqdn)   FQDN="${2:-}"; shift 2 ;;
      --yes)    ASSUME_YES=1; shift ;;
      -h|--help) usage; exit 0 ;;
      *)        usage; die "Unknown argument: $1" ;;
    esac
  done
  [[ ${MODE} =~ ^(precheck|install|postcheck|all)$ ]] || die "Invalid --mode: ${MODE}"
  [[ ${FQDN} =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]] \
    || die "--fqdn must be a lowercase FQDN (current: '${FQDN}')"
  if [[ ${MODE} =~ ^(install|all)$ ]]; then
    [[ -n ${BUNDLE} ]] || die "--bundle is required for mode ${MODE}"
  fi
  [[ -z ${BUNDLE} ]] || BUNDLE="$(readlink -f "${BUNDLE}")"
}

primary_ip() { ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}'; }

# ---------------- PRECHECK ----------------
check_user() {
  [[ ${EUID} -ne 0 ]] && pass "Running as non-root user ${USER}" || fail "Do not run as root (installer requirement)"
  if sudo -n true 2>/dev/null; then
    pass "sudo works without password"
  elif sudo -v; then
    pass "sudo works (password required - installer will ask for BECOME password)"
    BECOME_ARGS=(-K)
  else
    fail "User ${USER} has no sudo rights"
  fi
}

check_os() {
  # shellcheck disable=SC1091
  . /etc/os-release
  local major="${VERSION_ID%%.*}" minor="${VERSION_ID#*.}"
  if [[ ${ID} == "rhel" && ( ( ${major} == "9" && ${minor} -ge 6 ) || ${major} -ge 10 ) ]]; then
    pass "OS: ${PRETTY_NAME}"
  else
    fail "OS ${PRETTY_NAME} not supported (AAP 2.6 containerized needs RHEL 9.6+ or RHEL 10)"
  fi
  [[ $(uname -m) == "x86_64" ]] && pass "Arch x86_64" || warn "Arch $(uname -m) - ensure bundle matches"
}

check_subscription() {
  local st repos
  st=$(sudo subscription-manager status 2>/dev/null || true)
  [[ ${st} == *"Overall Status: Registered"* || ${st} == *"Simple Content Access"* ]] \
    && pass "RHEL registered" || fail "RHEL not registered (run: sudo subscription-manager register)"
  repos=$(sudo dnf -q repolist 2>/dev/null | awk 'NR>1 {print $1}' || true)
  if grep -q 'baseos' <<<"${repos}" && grep -q 'appstream' <<<"${repos}"; then
    pass "BaseOS and AppStream repos enabled"
  else
    fail "BaseOS/AppStream repos missing"
  fi
  local extra
  extra=$(grep -Ev 'baseos|appstream' <<<"${repos}" || true)
  [[ -z ${extra} ]] && pass "No extra repos" || warn "Extra repos enabled (Red Hat says only BaseOS/AppStream): ${extra//$'\n'/ }"
}

check_resources() {
  local cpu ram_gb root_free_gb vartmp_free_gb
  cpu=$(nproc)
  ram_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
  root_free_gb=$(df -BG --output=avail "${HOME}" | tail -1 | tr -dc '0-9')
  vartmp_free_gb=$(df -BG --output=avail /var/tmp | tail -1 | tr -dc '0-9')
  (( cpu >= MIN_CPU )) && pass "CPU ${cpu}" || fail "CPU ${cpu} < ${MIN_CPU}"
  (( ram_gb >= MIN_RAM_GB )) && pass "RAM ${ram_gb} GiB" || fail "RAM ${ram_gb} GiB < 16 GB"
  (( root_free_gb >= MIN_ROOT_FREE_GB )) && pass "Free disk for ${HOME}: ${root_free_gb} GiB" \
    || fail "Free disk ${root_free_gb} GiB < ${MIN_ROOT_FREE_GB} GiB"
  (( vartmp_free_gb >= MIN_VARTMP_FREE_GB )) && pass "/var/tmp free ${vartmp_free_gb} GiB" \
    || fail "/var/tmp free ${vartmp_free_gb} GiB < ${MIN_VARTMP_FREE_GB} GiB"
}

check_network() {
  local ip res
  ip=$(primary_ip)
  [[ -n ${ip} ]] && pass "Primary IPv4 ${ip}" || fail "No default IPv4 route"
  [[ $(hostname -f 2>/dev/null) == "${FQDN}" ]] && pass "hostname -f = ${FQDN}" \
    || warn "hostname -f is '$(hostname -f 2>/dev/null)'; install will set it to ${FQDN}"
  res=$(getent ahostsv4 "${FQDN}" | awk '{print $1; exit}' || true)
  if [[ -n ${res} && ${res} != 127.* ]]; then
    pass "${FQDN} resolves to ${res}"
  else
    warn "${FQDN} does not resolve to a LAN IP; install will add it to /etc/hosts"
  fi
  if ip -4 addr show scope global | grep -q dynamic; then
    warn "IPv4 is DHCP - reserve ${ip} on your router"
  else
    pass "IPv4 is static"
  fi
  [[ $(timedatectl show -p NTPSynchronized --value 2>/dev/null) == "yes" ]] \
    && pass "NTP synchronized" || warn "NTP not synchronized"
  if ss -ltnH "sport = :443" | grep -q .; then
    fail "Port 443 already in use"
  else
    pass "Port 443 free"
  fi
}

check_bundle() {
  if [[ -z ${BUNDLE} ]]; then
    info "Bundle check skipped (no --bundle)"
    return 0
  fi
  if [[ -f ${BUNDLE} && ${BUNDLE} == *containerized-setup-bundle-*.tar.gz ]]; then
    pass "Bundle file: $(basename "${BUNDLE}") ($(du -h "${BUNDLE}" | cut -f1))"
  else
    fail "Bundle not found or wrong name: ${BUNDLE} (need *containerized-setup-bundle-*.tar.gz)"
    return 0
  fi
  if tar -tzf "${BUNDLE}" >/dev/null 2>&1; then
    pass "Bundle archive is readable"
  else
    fail "Bundle archive is corrupt - re-download"
  fi
}

run_precheck() {
  info "===== PRECHECK ====="
  check_user
  check_os
  check_subscription
  check_resources
  check_network
  check_bundle
  info "Precheck result: ${FAILS} fail, ${WARNS} warn"
}

# ---------------- INSTALL ----------------
prepare_host() {
  local ip
  ip=$(primary_ip)
  if [[ $(hostname -f 2>/dev/null) != "${FQDN}" ]]; then
    sudo hostnamectl set-hostname "${FQDN}"
    info "Hostname set to ${FQDN}"
  fi
  if ! grep -Eq "^[0-9.]+[[:space:]]+${FQDN//./\\.}([[:space:]]|$)" /etc/hosts; then
    sudo cp -p /etc/hosts "/etc/hosts.bak-${TS}"
    printf '%s %s %s\n' "${ip}" "${FQDN}" "${FQDN%%.*}" | sudo tee -a /etc/hosts >/dev/null
    info "Added ${ip} ${FQDN} to /etc/hosts"
  fi
  sudo dnf -y install ansible-core tar
  sudo loginctl enable-linger "${USER}"
  pass "Linger enabled for ${USER} (containers survive logout/reboot)"
  if systemctl is-active --quiet firewalld; then
    sudo firewall-cmd --permanent --add-service=https >/dev/null
    sudo firewall-cmd --reload >/dev/null
    pass "firewalld: https (443/tcp) allowed"
  fi
}

extract_bundle() {
  local top
  mkdir -p "${WORK_DIR}"
  top=$(tar -tzf "${BUNDLE}" | head -1 | cut -d/ -f1 || true)
  [[ -n ${top} ]] || die "Cannot read top directory from bundle"
  INSTALL_DIR="${WORK_DIR}/${top}"
  if [[ -d ${INSTALL_DIR} ]]; then
    info "Bundle already extracted: ${INSTALL_DIR}"
  else
    info "Extracting bundle to ${WORK_DIR} (several minutes)"
    tar -xzf "${BUNDLE}" -C "${WORK_DIR}"
  fi
  [[ -f ${INSTALL_DIR}/inventory-growth ]] \
    || die "inventory-growth template not found in ${INSTALL_DIR} (files: $(ls "${INSTALL_DIR}" | tr '\n' ' '))"
  pass "Install dir: ${INSTALL_DIR}"
}

build_inventory() {
  local inv="${INSTALL_DIR}/${INV_NAME}" admin_pw
  if [[ -f ${inv} ]]; then
    info "Reusing existing ${inv} (passwords must not change on re-run)"
    return 0
  fi
  admin_pw=$(openssl rand -hex 12)
  local pool="" _
  for _ in $(seq 1 40); do pool+="$(openssl rand -hex 16) "; done

  (
    umask 077
    awk -v fqdn="${FQDN}" -v admin="${admin_pw}" -v bdir="${INSTALL_DIR}/bundle" -v pool="${pool}" '
      BEGIN { seen_bi = 0; seen_bd = 0; np = split(pool, pw, " "); ip = 0 }
      function rhex() { ip++; if (ip > np) { print "PASSWORD_POOL_EXHAUSTED" > "/dev/stderr"; exit 2 } return pw[ip] }
      { gsub(/aap\.example\.org/, fqdn) }
      /^[[:space:]]*registry_(username|password)[[:space:]]*=/ { print "# " $0 "   # not needed for bundle install"; next }
      /^[[:space:]]*bundle_install[[:space:]]*=/ { print "bundle_install=true"; seen_bi = 1; next }
      /^[[:space:]]*bundle_dir[[:space:]]*=/     { print "bundle_dir=" bdir; seen_bd = 1; next }
      /^[[:space:]]*hub_seed_collections[[:space:]]*=/ { print "hub_seed_collections=false"; next }
      /=[[:space:]]*<set your own>/ {
        split($0, kv, "=")
        key = kv[1]; gsub(/[[:space:]]/, "", key)
        if (key ~ /_admin_password$/ && key != "postgresql_admin_password") val = admin; else val = rhex()
        print key "=" val
        next
      }
      { print }
      END {
        if (!seen_bi) print "bundle_install=true"
        if (!seen_bd) print "bundle_dir=" bdir
      }
    ' "${INSTALL_DIR}/inventory-growth" > "${inv}"
  )

  if grep -nE '<[^>]+>' "${inv}" | grep -v '^[0-9]*:[[:space:]]*#'; then
    die "Unfilled placeholders remain in ${inv} (lines above) - edit manually, then re-run"
  fi
  grep -q "${FQDN}" "${inv}" || die "FQDN not present in ${inv}"

  (
    umask 077
    cat > "${CRED_FILE}" <<EOF
AAP_URL=https://${FQDN}/
AAP_ADMIN_USER=admin
AAP_ADMIN_PASSWORD=${admin_pw}
INVENTORY=${inv}
EOF
  )
  pass "Inventory ${inv} (600) and ${CRED_FILE} (600) written"
}

run_installer() {
  info "Running AAP installer (30-60 min on HDD)"
  ( cd "${INSTALL_DIR}" && ansible-playbook -i "${INV_NAME}" ansible.containerized_installer.install "${BECOME_ARGS[@]}" )
  pass "Installer playbook finished"
}

run_install() {
  info "===== INSTALL ====="
  confirm "Proceed with AAP install on ${FQDN}?" || die "Stopped by user"
  prepare_host
  extract_bundle
  build_inventory
  run_installer
}

# ---------------- POSTCHECK ----------------
run_postcheck() {
  info "===== POSTCHECK ====="
  FAILS=0; WARNS=0
  local ps_out stopped code_ping code_root
  ps_out=$(podman ps --format '{{.Names}} {{.Status}}' 2>/dev/null || true)
  if [[ -z ${ps_out} ]]; then
    fail "No running podman containers for user ${USER}"
  else
    printf '%s\n' "${ps_out}"
    pass "$(wc -l <<<"${ps_out}") containers running"
  fi
  stopped=$(podman ps -a --filter status=exited --format '{{.Names}} {{.Status}}' 2>/dev/null || true)
  [[ -z ${stopped} ]] || warn "Exited containers (may be normal one-shot tasks): ${stopped//$'\n'/; }"

  code_ping=$(curl -sk -o /dev/null -m 20 -w '%{http_code}' --resolve "${FQDN}:443:127.0.0.1" \
    "https://${FQDN}/api/gateway/v1/ping/" || true)
  code_root=$(curl -sk -o /dev/null -m 20 -w '%{http_code}' --resolve "${FQDN}:443:127.0.0.1" \
    "https://${FQDN}/" || true)
  if [[ ${code_ping} == "200" ]]; then
    pass "Gateway API ping HTTP 200"
  elif [[ ${code_root} =~ ^(200|301|302)$ ]]; then
    warn "UI responds (HTTP ${code_root}) but gateway ping returned ${code_ping} - verify in browser"
  else
    fail "UI not responding (ping ${code_ping}, root ${code_root})"
  fi

  [[ $(loginctl show-user "${USER}" -p Linger --value 2>/dev/null) == "yes" ]] \
    && pass "Linger enabled" || warn "Linger not enabled (run: sudo loginctl enable-linger ${USER})"

  info "URL:      https://${FQDN}/"
  info "User:     admin"
  info "Password: grep AAP_ADMIN_PASSWORD ${CRED_FILE}"
  info "Laptop hosts file: $(primary_ip) ${FQDN}"
  info "First login asks for subscription: use Red Hat login or a manifest"
  info "Postcheck result: ${FAILS} fail, ${WARNS} warn"
}

main() {
  parse_args "$@"
  exec > >(tee -a "${LOG_FILE}") 2>&1
  info "Mode=${MODE} FQDN=${FQDN} Log=${LOG_FILE}"
  INSTALL_DIR=""

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
