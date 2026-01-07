"""
Property-based tests for ASR Service Model Management Integrity
**Feature: faster-whisper-optimization, Property 1: Model Management Integrity**
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
"""

import os
import tempfile
import shutil
import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch, MagicMock
import sys
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.asr import ASRService, MODEL_CONFIGS


class TestASRModelManagementIntegrity:
    """Property-based tests for model management integrity"""
    
    @given(
        model_size=st.sampled_from(list(MODEL_CONFIGS.keys())),
        device=st.sampled_from(["auto", "cuda", "cpu"]),
        compute_type=st.sampled_from(["auto", "float16", "int8"])
    )
    @settings(max_examples=100)
    def test_model_management_integrity_property(self, model_size, device, compute_type):
        """
        Property 1: Model Management Integrity
        For any model download or loading operation, the system should correctly handle 
        model files, store them in the designated models directory, and provide 
        appropriate feedback when models are missing or corrupted.
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_models")
            
            # Test ASR service initialization with valid model size
            asr_service = ASRService(
                model_size=model_size,
                model_path=model_path,
                device=device,
                compute_type=compute_type
            )
            
            # Property: Service should be initialized with correct configuration
            assert asr_service.model_size == model_size
            assert asr_service.model_path == model_path
            assert asr_service.device == device
            assert asr_service.compute_type == compute_type
            assert asr_service.model is None  # Model not loaded yet
            
            # Property: Model info should be consistent with configuration
            model_info = asr_service.get_model_info()
            expected_config = MODEL_CONFIGS[model_size]
            
            assert model_info["model_size"] == model_size
            assert model_info["parameters"] == expected_config["parameters"]
            assert model_info["size_mb"] == expected_config["size_mb"]
            assert model_info["description"] == expected_config["description"]
            assert model_info["loaded"] is False
            
            # Property: Missing model should be detected correctly
            assert not asr_service._check_model_exists()
            
            # Property: Loading missing model should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                asr_service.load_model()
    
    @given(model_size=st.sampled_from(list(MODEL_CONFIGS.keys())))
    @settings(max_examples=50)
    def test_model_file_validation_property(self, model_size):
        """
        Property: Model file validation should correctly identify complete vs incomplete models
        **Validates: Requirements 2.1, 2.2, 2.5**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_models")
            os.makedirs(model_path, exist_ok=True)
            
            asr_service = ASRService(model_size=model_size, model_path=model_path)
            
            # Property: Empty directory should be detected as missing model
            assert not asr_service._check_model_exists()
            
            # Property: Partial model files should be detected as incomplete
            required_files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.json"]
            
            # Test with each file missing
            for missing_file in required_files:
                # Create all files except the missing one
                for file in required_files:
                    if file != missing_file:
                        file_path = os.path.join(model_path, file)
                        with open(file_path, 'w') as f:
                            if file == "config.json":
                                json.dump({"test": "config"}, f)
                            else:
                                f.write("test content")
                
                # Property: Missing any required file should result in incomplete model
                assert not asr_service._check_model_exists()
                
                # Clean up for next iteration
                for file in required_files:
                    file_path = os.path.join(model_path, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
            # Property: Complete model files should be detected as valid
            for file in required_files:
                file_path = os.path.join(model_path, file)
                with open(file_path, 'w') as f:
                    if file == "config.json":
                        json.dump({"test": "config"}, f)
                    else:
                        f.write("test content")
            
            assert asr_service._check_model_exists()
    
    @given(
        old_size=st.sampled_from(list(MODEL_CONFIGS.keys())),
        new_size=st.sampled_from(list(MODEL_CONFIGS.keys()))
    )
    @settings(max_examples=50)
    def test_model_switching_integrity_property(self, old_size, new_size):
        """
        Property: Model switching should maintain system integrity and handle failures gracefully
        **Validates: Requirements 2.3, 2.4**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_models")
            
            asr_service = ASRService(model_size=old_size, model_path=model_path)
            
            # Property: Initial state should be consistent
            assert asr_service.model_size == old_size
            original_model_path = asr_service.model_path
            
            # Property: Switching to same size should be idempotent
            if old_size == new_size:
                result = asr_service.switch_model_size(new_size)
                assert result is True
                assert asr_service.model_size == old_size  # Should remain unchanged
                assert asr_service.model_path == original_model_path
            
            # Property: Switching to different size should update configuration
            else:
                # Mock the load_model method to avoid actual model loading
                with patch.object(asr_service, 'load_model', return_value=True):
                    result = asr_service.switch_model_size(new_size)
                    assert result is True
                    assert asr_service.model_size == new_size
                
                # Test failure case - should rollback
                with patch.object(asr_service, 'load_model', return_value=False):
                    # Reset to original state
                    asr_service.model_size = old_size
                    result = asr_service.switch_model_size(new_size)
                    assert result is False
                    assert asr_service.model_size == old_size  # Should rollback
    
    @given(invalid_size=st.text().filter(lambda x: x not in MODEL_CONFIGS))
    @settings(max_examples=50)
    def test_invalid_model_size_handling_property(self, invalid_size):
        """
        Property: Invalid model sizes should be rejected with appropriate error messages
        **Validates: Requirements 2.1, 2.2**
        """
        assume(invalid_size.strip() != "")  # Avoid empty strings
        
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_models")
            
            # Property: Invalid model size should raise ValueError during initialization
            with pytest.raises(ValueError) as exc_info:
                ASRService(model_size=invalid_size, model_path=model_path)
            
            # Property: Error message should be informative
            error_message = str(exc_info.value)
            assert "不支持的模型大小" in error_message or "Unsupported model size" in error_message.lower()
            assert invalid_size in error_message
    
    @given(
        model_size=st.sampled_from(list(MODEL_CONFIGS.keys())),
        device=st.sampled_from(["auto", "cuda", "cpu"]),
        compute_type=st.sampled_from(["auto", "float16", "int8"])
    )
    @settings(max_examples=50)
    def test_device_compute_type_optimization_property(self, model_size, device, compute_type):
        """
        Property: Device and compute type optimization should follow consistent rules
        **Validates: Requirements 2.4, 2.5**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = os.path.join(temp_dir, "test_models")
            
            asr_service = ASRService(
                model_size=model_size,
                model_path=model_path,
                device=device,
                compute_type=compute_type
            )
            
            # Mock torch availability for consistent testing
            with patch('torch.cuda.is_available', return_value=True):
                optimal_device, optimal_compute_type = asr_service._determine_optimal_config()
                
                # Property: Auto device selection should prefer CUDA when available
                if device == "auto":
                    assert optimal_device == "cuda"
                else:
                    assert optimal_device == device
                
                # Property: Auto compute type should be optimized for device
                if compute_type == "auto":
                    if optimal_device == "cuda":
                        assert optimal_compute_type == "float16"
                    else:
                        assert optimal_compute_type == "int8"
                else:
                    # Property: CPU should not use float16
                    if optimal_device == "cpu" and compute_type == "float16":
                        assert optimal_compute_type == "int8"
                    else:
                        assert optimal_compute_type == compute_type
            
            # Test without CUDA
            with patch('torch.cuda.is_available', return_value=False):
                optimal_device, optimal_compute_type = asr_service._determine_optimal_config()
                
                # Property: Auto device selection should fallback to CPU when CUDA unavailable
                if device == "auto":
                    assert optimal_device == "cpu"
                
                # Property: CPU should always use int8 for compute type
                if optimal_device == "cpu":
                    assert optimal_compute_type == "int8"