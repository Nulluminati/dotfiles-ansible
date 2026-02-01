function synth --description "Claude Code backed by Synthetic.new Models"
  ANTHROPIC_BASE_URL=https://api.synthetic.new/anthropic \
  ANTHROPIC_AUTH_TOKEN="$SYNTHETIC_NEW_API_KEY" \
  ANTHROPIC_DEFAULT_OPUS_MODEL=hf:moonshotai/Kimi-K2.5 \
  ANTHROPIC_DEFAULT_SONNET_MODEL=hf:moonshotai/Kimi-K2.5 \
  ANTHROPIC_DEFAULT_HAIKU_MODEL=hf:moonshotai/Kimi-K2.5 \
  CLAUDE_CODE_SUBAGENT_MODEL=hf:moonshotai/Kimi-K2.5 \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \
  claude "$argv"
end
