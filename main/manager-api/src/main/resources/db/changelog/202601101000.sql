-- Remove deprecated LLM providers from ai_model_provider table
-- Removed providers: ollama, dify, coze, fastgpt, xinference, AliBL
-- These providers have been replaced with OpenAI-compatible alternatives
-- Date: 2026-01-10

DELETE FROM ai_model_provider WHERE id IN (
    'SYSTEM_LLM_ollama',
    'SYSTEM_LLM_dify',
    'SYSTEM_LLM_coze',
    'SYSTEM_LLM_fastgpt',
    'SYSTEM_LLM_xinference',
    'SYSTEM_LLM_AliBL'
);

-- Migration notes:
-- - Users with agents configured to use these providers should migrate to:
--   * Ollama users: use OpenAI-compatible endpoint (Ollama supports OpenAI API)
--   * Dify/FastGPT users: migrate to OpenAI or Gemini
--   * Coze users: migrate to OpenAI or Gemini
--   * Xinference users: use OpenAI-compatible endpoint (Xinference supports OpenAI API)
--   * AliBL users: use OpenAI with Aliyun Bailian base_url
--
-- - Optional: Uncomment below to delete model instances using removed providers
--   WARNING: This will delete all user-created models using these providers
-- DELETE FROM ai_model_config WHERE id IN (
--     SELECT m.id FROM ai_model_config m
--     WHERE m.config_json->>'$.type' IN ('ollama', 'dify', 'coze', 'fastgpt', 'xinference', 'AliBL')
-- );
