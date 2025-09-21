import React, { useState } from 'react';
import './QuestionForm.css';

const QuestionForm = ({ onAskQuestion, onExportReport, disabled }) => {
  const [question, setQuestion] = useState('');
  const [perSubK, setPerSubK] = useState(3);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim()) {
      onAskQuestion(question.trim(), perSubK);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleSubmit(e);
    }
  };

  const handleExport = () => {
    if (question.trim()) {
      onExportReport(question.trim());
    }
  };

  return (
    <div className="input-section">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="question">Research Question:</label>
          <textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter your research question here... (e.g., 'What are the best machine learning algorithms for image recognition?')"
            rows="4"
            disabled={disabled}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="perSubK">Documents per subquery:</label>
          <input
            type="number"
            id="perSubK"
            value={perSubK}
            onChange={(e) => setPerSubK(parseInt(e.target.value) || 3)}
            min="1"
            max="10"
            disabled={disabled}
          />
        </div>
        
        <div className="button-group">
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={disabled || !question.trim()}
          >
            Ask Question
          </button>
          <button 
            type="button" 
            className="btn btn-secondary"
            onClick={handleExport}
            disabled={disabled || !question.trim()}
          >
            Export Report
          </button>
        </div>
      </form>
    </div>
  );
};

export default QuestionForm;
