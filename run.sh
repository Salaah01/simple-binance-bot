#!/usr/bin/bash

usage() {
  echo "Usage ${0} -c [bh]" >&2
  echo "  -b  REBUILD       Rebuilds the docker services." >&2
  echo "  -c  TRADE_SYMBOL  Specify the trade/coin pair." >&2
  echo "  -h  HELP          So this message." >&2
}

while getopts c:bh OPTION; do
  case ${OPTION} in
  c)
    TRADE_SYMBOL="${OPTARG}"
    ;;
  b)
    REBUILD='--build'
    ;;
  h)
   usage
   exit 0
   ;;
  ?)
    usage
    exit 1
    ;;
  esac
done

if [[ -z "${TRADE_SYMBOL}" ]]; then
  usage
  exit 1
fi

cd "$(dirname $BASH_SOURCE[0])"

# Update environment variable.
export "TRADE_SYMBOL=${TRADE_SYMBOL}"
docker-compose up $REBUILD
