import React from 'react';
import ReactDOM from 'react-dom';
import { AppContainer } from 'react-hot-loader';
import ContactForm from './ContactForm';

const App = () => {
  return (
    <div>
      <h2>Contact Us</h2>
      <form>
        {/* Form fields and validation logic */}
      </form>
    </div>
  );
};

const Root = () => {
  return (
    <AppContainer>
      <App />
    </AppContainer>
  );
};

ReactDOM.render(<Root />, document.getElementById('root'));