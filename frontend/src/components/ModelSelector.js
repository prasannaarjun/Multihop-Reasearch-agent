import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ModelSelector.css';
import { apiService } from '../services/apiService';

const ModelSelector = ({ currentModel, onModelChange, disabled = false }) => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ollamaStatus, setOllamaStatus] = useState({ enabled: false, available: false });
  const dropdownRef = useRef(null);
  const modelsLoadedRef = useRef(false);

  const loadModels = useCallback(async () => {
    if (modelsLoadedRef.current) {
      console.log('Models already loaded, skipping API call');
      return; // Prevent multiple calls
    }
    
    console.log('Loading models from API...');
    setLoading(true);
    setError(null);
    try {
      const response = await apiService.getAvailableModels();
      
      setModels(response.models || []);
      setOllamaStatus({
        enabled: response.ollama_enabled,
        available: response.ollama_available
      });
      
      // Update current model from API response - use callback to avoid stale closure
      if (response.current_model) {
        onModelChange(response.current_model);
      }
      
      modelsLoadedRef.current = true; // Mark as loaded
    } catch (err) {
      setError(err.message || 'Failed to load models');
      console.error('Error loading models:', err);
    } finally {
      setLoading(false);
    }
  }, [onModelChange]); // Only include onModelChange, not currentModel

  // Only load models once on mount
  useEffect(() => {
    console.log('ModelSelector mounted, loading models...');
    loadModels();
    
    // Cleanup function to reset the loaded flag if component unmounts
    return () => {
      console.log('ModelSelector unmounting');
      modelsLoadedRef.current = false;
    };
  }, []); // Empty dependency array - only run on mount

  // Add a refresh function for manual refresh if needed
  const refreshModels = useCallback(() => {
    modelsLoadedRef.current = false;
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
