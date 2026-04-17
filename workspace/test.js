const { expect } = require('@jest/globals');
const App = require('./App');

describe('App', () => {
  it('renders feedback form with default values', () => {
    const { getByPlaceholderText, getByRole } = render(<App />);
    expect(getByPlaceholderText('Name')).toHaveValue('');
    expect(getByPlaceholderText('Feedback message')).toHaveValue('');
    expect(getByRole('star-rating')).toHaveAttribute('aria-label', 'Rating');
  });

  it('submits feedback with valid data', async () => {
    const { getByPlaceholderText, getByRole } = render(<App />);
    await fireEvent.change(getByPlaceholderText('Name'), { target: { value: 'John Doe' } });
    await fireEvent.change(getByPlaceholderText('Feedback message'), { target: { value: 'This is a test feedback.' } });
    await fireEvent.click(getByRole('button', { name: /Submit/i }));
    expect(await screen.findByText('Thank you for your feedback!')).toBeInTheDocument();
  });

  it('does not submit feedback with invalid data', async () => {
    const { getByPlaceholderText, getByRole } = render(<App />);
    await fireEvent.change(getByPlaceholderText('Name'), { target: { value: '' } });
    await fireEvent.click(getByRole('button', { name: /Submit/i }));
    expect(await screen.findByText('Please fill out the form correctly')).toBeInTheDocument();
  });
});