const { useState } = React;

function ContactForm() {
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    // Simulate API call
    await new Promise(r => setTimeout(r, 1200));
    setLoading(false);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="card">
        <div className="success">
          <div className="success-icon">✅</div>
          <h2>Message Sent!</h2>
          <p>Thanks <strong style={{color:'#60a5fa'}}>{form.name}</strong>, we'll get back to you at {form.email} shortly.</p>
          <button className="reset-btn" onClick={() => { setSubmitted(false); setForm({ name:'', email:'', phone:'', message:'' }); }}>
            Send Another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="badge"><span className="dot"></span> Agent Generated</div>
      <h1>Contact Us</h1>
      <p className="sub">Fill the form below and we'll get back to you within 24 hours.</p>

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Full Name</label>
          <input name="name" type="text" placeholder="John Doe" value={form.name} onChange={handleChange} required />
        </div>
        <div className="field">
          <label>Email Address</label>
          <input name="email" type="email" placeholder="john@example.com" value={form.email} onChange={handleChange} required />
        </div>
        <div className="field">
          <label>Phone Number</label>
          <input name="phone" type="tel" placeholder="+91 98765 43210" value={form.phone} onChange={handleChange} />
        </div>
        <div className="field">
          <label>Message</label>
          <textarea name="message" placeholder="Tell us how we can help you..." value={form.message} onChange={handleChange} required />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send Message →"}
        </button>
      </form>
    </div>
  );
}

// Render the component to the #root element
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<ContactForm />);