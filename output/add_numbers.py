# Define the add_numbers function
def add_numbers(num1, num2):
    """
    Adds two input numbers and returns the result.
    
    Args:
        num1 (int or float): The first number to add
        num2 (int or float): The second number to add
    
    Returns:
        int or float: The sum of num1 and num2
    
    Raises:
        TypeError: If either input is not a number
        OverflowError: If the result exceeds the maximum limit for integers
    """
    # Check if inputs are numeric
    if not isinstance(num1, (int, float)) or not isinstance(num2, (int, float)):
        raise TypeError("Both inputs must be numbers")
    
    # Perform addition with overflow checking
    try:
        result = num1 + num2
    except OverflowError:
        raise OverflowError("Result exceeds the maximum limit for integers")
    
    return result

# Example usage:
result = add_numbers(5, 7)
print(result)  # Output: 12

import unittest

class TestAddNumbers(unittest.TestCase):
    def test_add_integers(self):
        self.assertEqual(add_numbers(5, 7), 12)
    
    def test_add_floats(self):
        self.assertAlmostEqual(add_numbers(5.5, 7.7), 13.2)
    
    def test_invalid_input_type(self):
        with self.assertRaises(TypeError):
            add_numbers("five", 7)
    
    def test_overflow_error(self):
        with self.assertRaises(OverflowError):
            add_numbers(10**100, 1)

if __name__ == "__main__":
    unittest.main()
