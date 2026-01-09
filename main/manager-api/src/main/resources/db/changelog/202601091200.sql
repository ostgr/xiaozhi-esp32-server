-- Consolidate TTS providers to ElevenLabs only
-- This migration removes all non-ElevenLabs TTS providers and their associated configurations
-- keeping only ElevenLabs with support for all three streaming modes

-- Store voice IDs to delete (from non-ElevenLabs configs)
DELETE FROM `ai_tts_voice` WHERE `tts_model_id` IN (
  SELECT `id` FROM `ai_model_config`
  WHERE `model_type` = 'TTS'
  AND `model_code` NOT LIKE '%ElevenLabs%'
);

-- Remove all non-ElevenLabs TTS model configurations
DELETE FROM `ai_model_config`
WHERE `model_type` = 'TTS'
AND `model_code` NOT LIKE '%ElevenLabs%';

-- Remove all non-ElevenLabs TTS provider definitions
DELETE FROM `ai_model_provider`
WHERE `model_type` = 'TTS'
AND `provider_code` != 'elevenlabs_stream';

-- Update ElevenLabs provider to include interface_mode field in JSON configuration
UPDATE `ai_model_provider`
SET `fields` = JSON_SET(
  COALESCE(`fields`, '{}'),
  '$.interface_mode',
  JSON_OBJECT(
    'name', 'interface_mode',
    'label', 'Interface Mode',
    'type', 'string',
    'default', 'dual_stream',
    'required', false,
    'description', 'Streaming mode: dual_stream (WebSocket bidirectional), single_stream (HTTP streaming), non_stream (HTTP complete)',
    'options', JSON_ARRAY('dual_stream', 'single_stream', 'non_stream')
  )
)
WHERE `model_type` = 'TTS'
AND `provider_code` = 'elevenlabs_stream';
