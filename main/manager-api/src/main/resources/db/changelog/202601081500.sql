-- ElevenLabs Streaming TTS Provider
-- Adds ElevenLabs as the default TTS provider with dual-stream WebSocket support

-- Add ElevenLabs TTS Provider Definition
DELETE FROM `ai_model_provider` WHERE id = 'SYSTEM_TTS_ElevenLabsStreamTTS';
INSERT INTO `ai_model_provider` (`id`, `model_type`, `provider_code`, `name`, `fields`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('SYSTEM_TTS_ElevenLabsStreamTTS', 'TTS', 'elevenlabs_stream', 'ElevenLabs TTS (Streaming)',
'[{"key":"api_key","label":"API Key","type":"password"},{"key":"voice_id","label":"Voice ID","type":"string"},{"key":"model_id","label":"Model","type":"string"},{"key":"stability","label":"Stability (0-1)","type":"number"},{"key":"similarity_boost","label":"Similarity Boost (0-1)","type":"number"},{"key":"style","label":"Style (0-1)","type":"number"},{"key":"use_speaker_boost","label":"Use Speaker Boost","type":"boolean"},{"key":"output_format","label":"Output Format","type":"string"},{"key":"language_code","label":"Language Code","type":"string"},{"key":"enable_ws_reuse","label":"Enable WS Reuse","type":"boolean"},{"key":"output_dir","label":"Output Directory","type":"string"}]',
1, 1, NOW(), 1, NOW());

-- Add ElevenLabs TTS Model Configuration (set as default)
DELETE FROM `ai_model_config` WHERE id = 'TTS_ElevenLabsStreamTTS';
INSERT INTO `ai_model_config` (`id`, `model_type`, `model_code`, `model_name`, `is_default`, `is_enabled`, `config_json`, `doc_link`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
('TTS_ElevenLabsStreamTTS', 'TTS', 'ElevenLabsStreamTTS', 'ElevenLabs TTS (Streaming)',
1, 1,
'{"type":"elevenlabs_stream","api_key":"","voice_id":"21m00Tcm4TlvDq8ikWAM","model_id":"eleven_multilingual_v2","stability":0.5,"similarity_boost":0.75,"style":0.0,"use_speaker_boost":true,"output_format":"pcm_16000","language_code":"","enable_ws_reuse":true,"output_dir":"tmp/"}',
'https://elevenlabs.io/docs/api-reference/text-to-speech',
'ElevenLabs streaming TTS with dual-stream WebSocket support.\n\nModels:\n- eleven_multilingual_v2: Best quality, 29 languages (recommended)\n- eleven_turbo_v2_5: Fast, good quality\n- eleven_flash_v2_5: Fastest, real-time\n\nVoice Settings:\n- stability: 0-1, higher = more stable but potentially monotone\n- similarity_boost: 0-1, higher = closer to original voice\n- style: 0-1, higher = more expressive but less stable\n\nSupports Instant Voice Clone (IVC) - upload audio to create custom voices.',
1, 1, NOW(), 1, NOW());

-- Reset other TTS providers to not be default
UPDATE `ai_model_config` SET `is_default` = 0 WHERE `model_type` = 'TTS' AND `id` != 'TTS_ElevenLabsStreamTTS';

-- Add Default Voices (English and Vietnamese)
DELETE FROM `ai_tts_voice` WHERE tts_model_id = 'TTS_ElevenLabsStreamTTS';
INSERT INTO `ai_tts_voice` (`id`, `tts_model_id`, `name`, `tts_voice`, `languages`, `voice_demo`, `reference_audio`, `reference_text`, `remark`, `sort`, `creator`, `create_date`, `updater`, `update_date`) VALUES
-- English voices (pre-made from ElevenLabs)
('TTS_EL_Rachel', 'TTS_ElevenLabsStreamTTS', 'Rachel (Female)', 'zGjIP4SZlMnY9m93k97r', 'English', NULL, NULL, NULL, 'American female voice, calm and clear', 1, 1, NOW(), 1, NOW()),
('TTS_EL_Adam', 'TTS_ElevenLabsStreamTTS', 'Adam (Male)', '8JVbfL6oEdmuxKn5DK2C', 'English', NULL, NULL, NULL, 'American male voice, deep and authoritative', 2, 1, NOW(), 1, NOW()),
('TTS_EL_Bella', 'TTS_ElevenLabsStreamTTS', 'Bella (Female)', '1rnYMVDXZksVr6x7pZPX', 'English', NULL, NULL, NULL, 'American female voice, soft and friendly', 3, 1, NOW(), 1, NOW()),
('TTS_EL_Josh', 'TTS_ElevenLabsStreamTTS', 'Josh (Male)', 'rU18Fk3uSDhmg5Xh41o4', 'English', NULL, NULL, NULL, 'American male voice, young and energetic', 4, 1, NOW(), 1, NOW()),
-- Vietnamese voices (from ElevenLabs Voice Library - use eleven_multilingual_v2 model)
-- Note: These voice_ids are placeholders. Search in ElevenLabs Voice Library for actual Vietnamese voices
('TTS_EL_Vi_Linh', 'TTS_ElevenLabsStreamTTS', 'Mai (Nu Viet)', 'd5HVupAWCwe4e6GvMCAL', 'Vietnamese', NULL, NULL, NULL, 'Vietnamese female voice', 5, 1, NOW(), 1, NOW()),
('TTS_EL_Vi_Minh', 'TTS_ElevenLabsStreamTTS', 'Minh (Nam Viet)', 'XBDAUT8ybuJTTCoOLSUj', 'Vietnamese', NULL, NULL, NULL, 'Vietnamese male voice', 6, 1, NOW(), 1, NOW()),
('TTS_EL_Vi_Lan', 'TTS_ElevenLabsStreamTTS', 'Lan (Nu Viet)', '2wMoasbnkroyeaj9FYxI', 'Vietnamese', NULL, NULL, NULL, 'Vietnamese female voice', 7, 1, NOW(), 1, NOW()),
('TTS_EL_Vi_Hung', 'TTS_ElevenLabsStreamTTS', 'Hung (Nam Viet)', 'UsgbMVmY3U59ijwK5mdh', 'Vietnamese', NULL, NULL, NULL, 'Vietnamese male voice', 8, 1, NOW(), 1, NOW());
