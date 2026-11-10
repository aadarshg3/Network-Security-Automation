#!/usr/bin/env bash
# Report ansible-core, Python and required Python libraries inside an AAP or AWX execution environment.
# Usage: ./ee_check.sh aap [image]   |   ./ee_check.sh awx
set -Eeuo pipefail

PLATFORM="${1:-}"
IMAGE="${2:-}"

read -r -d '' PROBE <<'PY' || true
PY=$(ansible --version | awk '/python version/ {print $NF}' | tr -d '()[]')
[[ -x ${PY} ]] || PY=python3
ansible --version | head -1
"${PY}" --version
for m in paramiko pylibsshext ncclient scp grpc lxml xmltodict jxmlease \
         catalystcentersdk pytz meraki catalystwan \
         requests_toolbelt jsonpath_ng xmljson OpenSSL dateutil pydantic \
         nac_yaml nac_validate macaddress netaddr jmespath; do
  if "${PY}" -c "import ${m}" 2>/dev/null; then echo "OK      ${m}"; else echo "MISSING ${m}"; fi
done
PY

case "${PLATFORM}" in
  aap)
    if [[ -z ${IMAGE} ]]; then
      echo "Available EE images:"
      podman images --format '{{.Repository}}:{{.Tag}}' | grep -i 'ee' || true
      echo "Re-run: $0 aap <image>"
      exit 1
    fi
    podman run --rm "${IMAGE}" bash -c "${PROBE}"
    ;;
  awx)
    /usr/local/bin/kubectl -n awx exec deploy/awx-task -c awx-ee -- bash -c "${PROBE}"
    ;;
  *)
    echo "Usage: $0 aap [image] | $0 awx"
    exit 1
    ;;
esac
