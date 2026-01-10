-- 更新ai_model_provider的fields字段，将type为dict的改为string
-- NOTE: fastgpt provider was removed in migration 202601101000_remove_deprecated_llm_providers
update ai_model_provider set fields = replace(fields, '"type": "dict"', '"type": "string"') where id not in ('SYSTEM_TTS_custom');
update ai_model_provider set fields = replace(fields, '"type":"dict"', '"type": "string"') where id not in ('SYSTEM_TTS_custom');