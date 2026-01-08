-- Remove all VAD and ASR providers to prepare for Deepgram integration
-- This migration removes all existing Voice Activity Detection (VAD) and Automatic Speech Recognition (ASR) providers
-- while keeping the database schema intact for future Deepgram provider addition

-- Remove all VAD (Voice Activity Detection) providers
-- Removes: SileroVAD
DELETE FROM `ai_model_provider` WHERE `model_type` = 'VAD';
DELETE FROM `ai_model_config` WHERE `model_type` = 'VAD';

-- Remove all ASR (Automatic Speech Recognition) providers
-- Removes: FunASR, FunASRServer, SherpaASR, DoubaoASR, DoubaoStreamASR, TencentASR,
--          AliyunASR, AliyunStreamASR, AliyunBLStream, BaiduASR, XunfeiStream,
--          OpenaiASR, VoskASR, Qwen3Flash
DELETE FROM `ai_model_provider` WHERE `model_type` = 'ASR';
DELETE FROM `ai_model_config` WHERE `model_type` = 'ASR';
