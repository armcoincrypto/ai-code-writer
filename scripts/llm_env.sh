# Usage: source scripts/llm_env.sh; llm_local   # or: llm_cloud
llm_local() {
  export OPENAI_BASE_URL="http://127.0.0.1:11434/v1"
  export OPENAI_API_KEY="ollama"
  echo "✅ Using Ollama (local) — $OPENAI_BASE_URL"
}
llm_cloud() {
  unset OPENAI_BASE_URL
  set -o allexport; source .env.local; set +o allexport
  echo "✅ Using OpenAI cloud (default base URL)"
}
llm_custom() {
  # For OpenAI-compatible endpoints (like your synthetic.new URL)
  # Edit these two lines or set them before calling `llm_custom`.
  : "${OPENAI_BASE_URL:?set OPENAI_BASE_URL first}"
  : "${OPENAI_API_KEY:?set OPENAI_API_KEY first}"
  echo "✅ Using custom endpoint — $OPENAI_BASE_URL"
}
