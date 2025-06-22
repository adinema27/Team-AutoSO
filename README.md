# 🧠 AutoSO – AI-Powered Sales Order Generator

AutoSO is a simulated, intelligent Sales Order system inspired by SAP ECC SD module. It leverages machine learning and natural language processing to automatically assign financial fields like **Terms of Payment**, **Discount Percentage**, and **Dunning Procedure** based on customer history and behavior.

---

## 🚀 How It Works

- Users **manually enter**:
  - Customer Number (CN)
  - Material Number (MN)
  - Quantity

- The system:
  - Checks stock availability from a simulated Material Master CSV.
  - Analyzes the customer's profile from Customer Master CSV.
  - Uses a trained ML model to predict:
    - Terms of Payment (in days)
    - Discount Percentage
    - Dunning Level

- The new sales order is then:
  - Displayed with AI-suggested fields
  - Appended to a persistent `sales_orders.csv` file
  - Stock and customer data is updated accordingly

---

## 🛠️ Tech Stack

- **Backend**: Python, Django or Flask
- **ML Model**: Scikit-learn (MultiOutputRegressor with RandomForest)
- **Data Storage**: CSV (Customer, Material, and Order)
- **NLP (optional)**: spaCy or OpenAI LLM for prompt extraction
- **Frontend**: HTML/CSS/JS or Django Templates

---

## 📂 Data Files

- `customer_data.csv` – Contains customer history (invoices, payment days, tenure, etc.)
- `stock_data.csv` – Simulated material stock availability
- `sales_orders.csv` – Appends every newly created sales order

---

## 📦 Setup Instructions

```bash
cd autoso
pip install -r requirements.txt
python app.py  # or run your Django server
