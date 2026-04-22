#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.example"

if [[ ! -f "$ENV_EXAMPLE" ]]; then
  echo "Missing .env.example in $ROOT_DIR"
  exit 1
fi

prompt_with_default() {
  local label="$1"
  local default_value="$2"
  local user_value

  read -r -p "$label [$default_value]: " user_value
  if [[ -z "$user_value" ]]; then
    printf '%s' "$default_value"
  else
    printf '%s' "$user_value"
  fi
}

prompt_yes_no() {
  local label="$1"
  local default_value="$2"
  local user_value
  local normalized_default="$default_value"

  read -r -p "$label [$default_value]: " user_value
  if [[ -z "$user_value" ]]; then
    user_value="$normalized_default"
  fi

  case "${user_value,,}" in
    y|yes|true|1|on) printf 'true' ;;
    n|no|false|0|off) printf 'false' ;;
    *)
      echo "Please answer yes/no, true/false, on/off, or 1/0." >&2
      exit 1
      ;;
  esac
}

echo
echo "BTC Proxy Demo Bot Installer"
echo "Workspace: $ROOT_DIR"
echo

overwrite="yes"
if [[ -f "$ENV_FILE" ]]; then
  overwrite="$(prompt_yes_no ".env already exists. Overwrite?" "no")"
  if [[ "$overwrite" != "true" ]]; then
    echo "Keeping existing .env"
    exit 0
  fi
fi

bot_mode="$(prompt_with_default "Bot mode (dry_run/demo)" "dry_run")"
strategy_label="$(prompt_with_default "Strategy label" "cbBTC BTC proxy demo")"
local_live_loop="$(prompt_yes_no "Enable local live loop?" "yes")"
poll_interval_seconds="$(prompt_with_default "Polling interval in seconds" "30")"
max_loop_iterations="$(prompt_with_default "Max loop iterations (0 = unlimited)" "0")"
paper_trade_size_usdc="$(prompt_with_default "Paper trade size in USDC" "1000")"
fee_bps="$(prompt_with_default "Fee in basis points" "0")"
history_limit="$(prompt_with_default "History candle limit" "250")"
signal_timeframe="$(prompt_with_default "Signal timeframe" "5m")"
trend_timeframe="$(prompt_with_default "Trend timeframe" "30m")"
data_dir="$(prompt_with_default "Data directory" "data")"

demo_account_count="0"
demo_block=""

if [[ "$bot_mode" == "demo" ]]; then
  demo_account_count="$(prompt_with_default "Demo account count" "1")"
  if ! [[ "$demo_account_count" =~ ^[0-9]+$ ]]; then
    echo "Demo account count must be an integer."
    exit 1
  fi

  if [[ "$demo_account_count" -eq 0 ]]; then
    echo "Demo account count cannot be 0 in demo mode."
    exit 1
  fi

  for ((i=1; i<=demo_account_count; i++)); do
    demo_name="$(prompt_with_default "Demo account $i name" "demo_$i")"
    demo_api_key="$(prompt_with_default "Demo account $i API key" "dummy_key_$i")"
    demo_api_secret="$(prompt_with_default "Demo account $i API secret" "dummy_secret_$i")"
    demo_block+=$'\n'
    demo_block+="DEMO_${i}_NAME=${demo_name}"$'\n'
    demo_block+="DEMO_${i}_API_KEY=${demo_api_key}"$'\n'
    demo_block+="DEMO_${i}_API_SECRET=${demo_api_secret}"$'\n'
  done
fi

cat > "$ENV_FILE" <<EOF
BOT_MODE=$bot_mode
SYMBOL=cbBTC/USDC
STRATEGY_LABEL=$strategy_label
DATA_SOURCE=meteora
METEORA_POOL_ADDRESS=7ubS3GccjhQY99AYNKXjNJqnXjaokEdfdV915xnCb96r
METEORA_POOL_NAME=cbBTC-USDC
SIGNAL_TIMEFRAME=$signal_timeframe
TREND_TIMEFRAME=$trend_timeframe
HISTORY_LIMIT=$history_limit
LOCAL_LIVE_LOOP=$local_live_loop
POLL_INTERVAL_SECONDS=$poll_interval_seconds
MAX_LOOP_ITERATIONS=$max_loop_iterations
DATA_DIR=$data_dir
PAPER_TRADE_SIZE_USDC=$paper_trade_size_usdc
FEE_BPS=$fee_bps
DEMO_ACCOUNT_COUNT=$demo_account_count$demo_block
EOF

echo
echo "Created $ENV_FILE"
echo
echo "Next steps:"
echo "1. Review .env if needed"
echo "2. Run: python3 -m app.main"
echo
