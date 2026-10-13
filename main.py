import sqlite3
from pathlib import Path

import pandas as pd


database = Path(__file__).resolve().parent / "data.sqlite"
conn = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)

# Boston employees.
df_boston = pd.read_sql("""
    SELECT e.firstName, e.lastName
    FROM employees AS e
    JOIN offices AS o ON e.officeCode = o.officeCode
    WHERE o.city = 'Boston'
    ORDER BY e.firstName, e.lastName;
""", conn)

# Count employee IDs rather than rows so empty offices count as zero.
df_zero_emp = pd.read_sql("""
    SELECT o.officeCode, o.city,
           COUNT(e.employeeNumber) AS n_employees
    FROM offices AS o
    LEFT JOIN employees AS e ON o.officeCode = e.officeCode
    GROUP BY o.officeCode, o.city
    HAVING COUNT(e.employeeNumber) = 0;
""", conn)

df_employee = pd.read_sql("""
    SELECT e.firstName, e.lastName, o.city, o.state
    FROM employees AS e
    LEFT JOIN offices AS o ON e.officeCode = o.officeCode
    ORDER BY e.firstName, e.lastName;
""", conn)

df_contacts = pd.read_sql("""
    SELECT c.contactFirstName, c.contactLastName,
           c.phone, c.salesRepEmployeeNumber
    FROM customers AS c
    LEFT JOIN orders AS o ON c.customerNumber = o.customerNumber
    WHERE o.orderNumber IS NULL
    ORDER BY c.contactLastName, c.contactFirstName;
""", conn)

df_payment = pd.read_sql("""
    SELECT c.contactFirstName, c.contactLastName,
           p.amount, p.paymentDate
    FROM customers AS c
    JOIN payments AS p ON c.customerNumber = p.customerNumber
    ORDER BY CAST(p.amount AS REAL) DESC;
""", conn)

df_credit = pd.read_sql("""
    SELECT e.employeeNumber, e.firstName, e.lastName,
           COUNT(c.customerNumber) AS n_customers
    FROM employees AS e
    JOIN customers AS c
      ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY e.employeeNumber, e.firstName, e.lastName
    HAVING AVG(CAST(c.creditLimit AS REAL)) > 90000
    ORDER BY n_customers DESC, e.employeeNumber;
""", conn)

df_product_sold = pd.read_sql("""
    SELECT p.productName,
           COUNT(DISTINCT od.orderNumber) AS numorders,
           SUM(od.quantityOrdered) AS totalunits
    FROM products AS p
    JOIN orderDetails AS od ON p.productCode = od.productCode
    GROUP BY p.productCode, p.productName
    ORDER BY totalunits DESC, p.productCode;
""", conn)

df_total_customers = pd.read_sql("""
    SELECT p.productName, p.productCode,
           COUNT(DISTINCT o.customerNumber) AS numpurchasers
    FROM products AS p
    JOIN orderDetails AS od ON p.productCode = od.productCode
    JOIN orders AS o ON od.orderNumber = o.orderNumber
    GROUP BY p.productCode, p.productName
    ORDER BY numpurchasers DESC, p.productCode;
""", conn)

df_customers = pd.read_sql("""
    SELECT COUNT(c.customerNumber) AS n_customers,
           o.officeCode, o.city
    FROM offices AS o
    LEFT JOIN employees AS e ON o.officeCode = e.officeCode
    LEFT JOIN customers AS c
      ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY o.officeCode, o.city
    ORDER BY o.officeCode;
""", conn)

# Return each qualifying employee once, even across multiple sales.
df_under_20 = pd.read_sql("""
    SELECT DISTINCT e.employeeNumber, e.firstName, e.lastName,
                    office.city, office.officeCode
    FROM employees AS e
    JOIN offices AS office ON e.officeCode = office.officeCode
    JOIN customers AS c
      ON e.employeeNumber = c.salesRepEmployeeNumber
    JOIN orders AS o ON c.customerNumber = o.customerNumber
    JOIN orderDetails AS od ON o.orderNumber = od.orderNumber
    WHERE od.productCode IN (
        SELECT detail.productCode
        FROM orderDetails AS detail
        JOIN orders AS purchase
          ON detail.orderNumber = purchase.orderNumber
        GROUP BY detail.productCode
        HAVING COUNT(DISTINCT purchase.customerNumber) < 20
     )
    ORDER BY e.lastName, e.firstName, e.employeeNumber;
""", conn)

conn.close()