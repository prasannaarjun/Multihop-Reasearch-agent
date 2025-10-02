import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ModelSelector.css';
import { apiService } from '../services/apiService';

const ModelSelector = ({ currentModel, onModelChange, disabled = false }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ollamaStatus, setOllamaStatus] = useState({ enabled: false, available: false });
  const dropdownRef = useRef(null);

  const loadModels = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getAvailableModels();
      
      setModels(response.models || []);
      setOllamaStatus({
        enabled: response.ollama_enabled,
        available: response.ollama_available
      });
      
      // Update current model from API response
      if (response.current_model && response.current_model !== currentModel) {
        onModelChange(response.current_model);
      }
    } catch (err) {
      setError(err.message || 'Failed to load models');
      console.error('Error loading models:', err);
    } finally {
      setLoading(false);
    }
  }, [currentModel, onModelChange]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const handleModelSelect = async (modelName) => {
    if (modelName === currentModel || disabled) return;

    try {
      await apiService.changeModel(modelName);
      onModelChange(modelName);
    } catch (err) {
      setError(err.message || 'Failed to change model');
      console.error('Error changing model:', err);
    }
  };

  if (!ollamaStatus.enabled) {
    return (
      <div className="model-selector-disabled">
        <span>Ollama not enabled</span>
      </div>
    );
  }

  if (!ollamaStatus.available) {
    return (
      <div className="model-selector-disabled">
        <span>Ollama not running</span>
      </div>
    );
  }

  return (
    <div className="model-selector" ref={dropdownRef}>
      <select
        id="model-selector"
        name="model"
        value={currentModel || ""}
        onChange={(e) => handleModelSelect(e.target.value)}
        disabled={disabled || loading}
        className="model-select"
      >
        {loading ? (
          <option value="">Loading models...</option>
        ) : error ? (
          <option value="">Error loading models</option>
        ) : models.length === 0 ? (
          <option value="">No models available</option>
        ) : (
          <>
            <option value="">Select a model...</option>
            {models.map((model) => (
              <option key={model.name} value={model.name}>
                {model.name || 'Unnamed Model'}
              </option>
            ))}
          </>
        )}
      </select>
    </div>
  );
};

export default ModelSelector;
