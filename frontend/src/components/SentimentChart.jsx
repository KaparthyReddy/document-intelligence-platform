import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { getSentimentEmoji } from '../utils/helpers';
import './SentimentChart.css';

const SentimentChart = ({ analysis }) => {
  const sentiment = analysis?.sentiment || {};
  
  const pieData = [
    { name: 'Positive', value: sentiment.positive_chunks || 0, color: '#10b981' },
    { name: 'Negative', value: sentiment.negative_chunks || 0, color: '#ef4444' },
    { name: 'Neutral', value: sentiment.neutral_chunks || 0, color: '#94a3b8' },
  ].filter(item => item.value > 0);

  const overallSentiment = sentiment.overall_sentiment || 'neutral';
  const averageScore = sentiment.average_score || 0;

  return (
    <div className="sentiment-chart">
      {/* Overall Sentiment */}
      <div className="sentiment-header">
        <div className="sentiment-card main">
          <div className="sentiment-emoji">
            {getSentimentEmoji(overallSentiment)}
          </div>
          <div className="sentiment-info">
            <div className="sentiment-label">Overall Sentiment</div>
            <div className="sentiment-value" style={{
              color: overallSentiment === 'positive' ? '#10b981' :
                     overallSentiment === 'negative' ? '#ef4444' : '#94a3b8'
            }}>
              {overallSentiment.toUpperCase()}
            </div>
            <div className="sentiment-score">
              Score: {averageScore.toFixed(2)}
            </div>
          </div>
        </div>

        <div className="sentiment-stats">
          <div className="stat-item positive">
            <div className="stat-label">Positive Chunks</div>
            <div className="stat-value">{sentiment.positive_chunks || 0}</div>
          </div>
          <div className="stat-item negative">
            <div className="stat-label">Negative Chunks</div>
            <div className="stat-value">{sentiment.negative_chunks || 0}</div>
          </div>
          <div className="stat-item neutral">
            <div className="stat-label">Neutral Chunks</div>
            <div className="stat-value">{sentiment.neutral_chunks || 0}</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Pie Chart */}
        <div className="card chart-card">
          <h3>📊 Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar Chart */}
        <div className="card chart-card">
          <h3>📈 Chunk Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={pieData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#475569" />
              <XAxis dataKey="name" stroke="#cbd5e1" />
              <YAxis stroke="#cbd5e1" />
              <Tooltip 
                contentStyle={{
                  background: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                  color: '#f1f5f9'
                }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Insights */}
      <div className="card">
        <h3>💡 Sentiment Insights</h3>
        <div className="insights-list">
          <div className="insight-item">
            <span className="insight-icon">📊</span>
            <div>
              <strong>Total Chunks Analyzed:</strong> {sentiment.total_chunks || 0}
            </div>
          </div>
          
          {sentiment.positive_chunks > sentiment.negative_chunks && (
            <div className="insight-item positive">
              <span className="insight-icon">✅</span>
              <div>
                The document has a <strong>predominantly positive</strong> tone with {sentiment.positive_chunks} positive chunks
              </div>
            </div>
          )}
          
          {sentiment.negative_chunks > sentiment.positive_chunks && (
            <div className="insight-item negative">
              <span className="insight-icon">⚠️</span>
              <div>
                The document has a <strong>predominantly negative</strong> tone with {sentiment.negative_chunks} negative chunks
              </div>
            </div>
          )}
          
          {sentiment.neutral_chunks > (sentiment.positive_chunks + sentiment.negative_chunks) && (
            <div className="insight-item neutral">
              <span className="insight-icon">ℹ️</span>
              <div>
                The document has a <strong>mostly neutral</strong> tone with {sentiment.neutral_chunks} neutral chunks
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SentimentChart;