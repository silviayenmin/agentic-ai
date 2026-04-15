import math

def calculate_area(radius):
    area = math.pi * (radius ** 2)
    return area

def main():
    radius = float(input("Enter the radius of the circle: "))
    if radius < 0:
        print("Invalid input. Radius cannot be negative.")
    else:
        calculated_area = calculate_area(radius)
        print(f"The area of the circle is {calculated_area:.2f} square units.")

if __name__ == "__main__":
    main()