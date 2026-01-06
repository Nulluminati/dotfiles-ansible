function zai --description "Claude Code backed by Z.AI GLM Models"
  ANTHROPIC_DEFAULT_OPUS_MODEL=GLM-4.7 \
  ANTHROPIC_DEFAULT_SONNET_MODEL=GLM-4.7 \
  ANTHROPIC_DEFAULT_HAIKU_MODEL=GLM-4.5-Air \
  ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic \
  ANTHROPIC_AUTH_TOKEN="$ZAI_API_KEY" \
  claude "$argv"
end
