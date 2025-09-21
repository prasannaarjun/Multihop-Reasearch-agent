import React from 'react';
import './Results.css';

const Results = ({ data }) => {
  const formatAnswer = (answer) => {
    return answer.split('\n').map((line, index) => (
      <span key={index}>
        {line}
        {index < answer.split('\n').length - 1 && <br />}
      </span>
    ));
  };

  const formatSubqueries = (subqueries) => {
    if (!subqueries || subqueries.length === 0) {
      return <p>No subqueries processed.</p>;
    }

    return (
      <div>
        <h3>Research Process</h3>
        {subqueries.map((subquery, index) => (
          <div key={index} className="subquery">
            <h4>{index + 1}. {subquery.subquery}</h4>
            <p>{subquery.summary}</p>
          </div>
        ))}
      </div>
    );
  };

  const formatCitations = (citations) => {
    if (!citations || citations.length === 0) {
      return <p>No sources found.</p>;
    }

    return (
      <div>
        <h3>Sources Consulted</h3>
        {citations.map((citation, index) => (
          <div key={index} className="citation">
            <h5>{citation.title}</h5>
            <div className="score">Relevance: {citation.score.toFixed(3)}</div>
            <div className="filename">File: {citation.filename}</div>
            <div className="snippet">{citation.snippet}</div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="results">
      <h2>Research Results</h2>
      
      <div className="answer">
        <div className="answer-content">
          {formatAnswer(data.answer)}
        </div>
      </div>

      <div className="subqueries">
        {formatSubqueries(data.subqueries)}
      </div>

      <div className="citations">
        {formatCitations(data.citations)}
      </div>
    </div>
  );
};

export default Results;
