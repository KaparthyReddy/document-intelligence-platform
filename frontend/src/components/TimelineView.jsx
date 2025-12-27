import React from 'react';
import './TimelineView.css';

const TimelineView = ({ analysis }) => {
  const timeline = analysis?.timeline || [];
  const dates = analysis?.dates || [];

  if (timeline.length === 0 && dates.length === 0) {
    return (
      <div className="card">
        <div className="empty-timeline">
          <div className="empty-icon">⏱️</div>
          <h3>No Timeline Data</h3>
          <p>No dates or temporal events were found in this document</p>
        </div>
      </div>
    );
  }

  return (
    <div className="timeline-view">
      {/* Summary */}
      <div className="timeline-summary">
        <div className="summary-card">
          <div className="summary-icon">📅</div>
          <div>
            <div className="summary-value">{dates.length}</div>
            <div className="summary-label">Dates Found</div>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">⏱️</div>
          <div>
            <div className="summary-value">{timeline.length}</div>
            <div className="summary-label">Timeline Events</div>
          </div>
        </div>
      </div>

      {/* Timeline */}
      {timeline.length > 0 && (
        <div className="card">
          <h3>⏱️ Event Timeline</h3>
          <div className="timeline-container">
            {timeline.map((event, idx) => (
              <div key={idx} className="timeline-event">
                <div className="timeline-marker">
                  <div className="marker-dot" />
                  {idx < timeline.length - 1 && <div className="marker-line" />}
                </div>
                <div className="timeline-content">
                  <div className="event-date">{event.date}</div>
                  {event.related_entities && event.related_entities.length > 0 && (
                    <div className="event-entities">
                      <strong>Related:</strong>{' '}
                      {event.related_entities.join(', ')}
                    </div>
                  )}
                  <div className="event-context">{event.context}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Dates */}
      {dates.length > 0 && (
        <div className="card">
          <h3>📅 All Dates Mentioned</h3>
          <div className="dates-grid">
            {dates.map((date, idx) => (
              <div key={idx} className="date-card">
                <div className="date-icon">📅</div>
                <div className="date-text">{date.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TimelineView;