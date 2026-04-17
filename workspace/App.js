import React, { useState } from 'react';
import ReactDOM from 'react-dom';

function App() {
  const [name, setName] = useState('');
  const [rating, setRating] = useState(0);
  const [category, setCategory] = useState('');

  function handleSubmit(event) {
    event.preventDefault();
    if (name === '' || rating < 1 || rating > 5) {
      alert('Please fill out the form correctly');
    } else {
      // Send data to API endpoint
      fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, rating, category }),
      })
        .then((response) => response.json())
        .then((data) => console.log(data))
        .catch((error) => console.error(error));
    }
  }

  return (
    <div className="feedback-form">
      <h2>Leave Your Feedbackzzz</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input type="text" value={name} onChange={(event) => setName(event.target.value)} />
        </label>
        <br />
        <label>
          Star Rating (1-5):
          <select value={rating} onChange={(event) => setRating(Number(event.target.value))}>
            {Array.from({ length: 5 }, (_, i) => i + 1).map((i) => (
              <option key={i}>{i}</option>
            ))}
          </select>
        </label>
        <br />
        <label>
          Category:
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="Bug">Bug</option>
            <option value="Suggestion">Suggestion</option>
            <option value="Complaint">Complaint</option>
          </select>
        </label>
        <br />
        <button type="submit">Submit Feedback</button>
      </form>
    </div>
  );
}

ReactDOM.render(<App />, document.getElementById('root'));