from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import joblib
import os
from datetime import datetime
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'loyalty_model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')
CUSTOMER_CSV = os.path.join(BASE_DIR, 'customer.csv')
MATERIAL_CSV = os.path.join(BASE_DIR, 'material.csv')
SALESORDER_CSV = os.path.join(BASE_DIR, 'salesorder.csv')

# Load model and scaler once
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    model = None
    scaler = None
    print(f"Model loading error: {e}")

def to_native_types(data):
    for key in data:
        if isinstance(data[key], (np.integer, np.int64)):
            data[key] = int(data[key])
        elif isinstance(data[key], (np.floating, np.float64)):
            data[key] = float(data[key])
    return data

@csrf_exempt
def create_sales_order_view(request):
    if request.method == 'POST':
        try:
            customer_number = request.POST.get('customer_number', '').strip()
            material_number = request.POST.get('material_number', '').strip()
            quantity = int(request.POST.get('quantity', '0'))

            if quantity <= 0:
                return render(request, 'prompt_form.html', {'error': '❌ Quantity must be greater than zero.'})

            customer_df = pd.read_csv(CUSTOMER_CSV)
            material_df = pd.read_csv(MATERIAL_CSV)

            if customer_number not in customer_df['Customer_Number'].astype(str).values:
                return render(request, 'prompt_form.html', {'error': '❌ Invalid customer number.'})
            if material_number not in material_df['Material Number'].astype(str).values:
                return render(request, 'prompt_form.html', {'error': '❌ Invalid material number.'})

            customer = customer_df[customer_df['Customer_Number'].astype(str) == customer_number].iloc[0]
            material = material_df[material_df['Material Number'].astype(str) == material_number].iloc[0]

            try:
                available_stock = int(material['stock'])
            except:
                return render(request, 'prompt_form.html', {'error': '⚠️ Stock data is invalid or missing.'})

            if quantity > available_stock:
                return render(request, 'prompt_form.html', {
                    'error': f"❌ Insufficient stock. Only {available_stock} units available."
                })

            model_input = scaler.transform([[customer['Number_of_Open_Invoices'],
                                             customer['Period'],
                                             customer['Period']]])
            prediction = model.predict(model_input)[0]

            context = {
                'customer_number': customer_number,
                'material_number': material_number,
                'quantity': quantity,
                'term_of_payment': round(prediction[0], 2),
                'discount': round(prediction[1], 2),
                'dunning_level': int(round(prediction[2]))
            }

            request.session['order_data'] = to_native_types(context)
            return redirect('order_summary')

        except Exception as e:
            return render(request, 'prompt_form.html', {
                'error': f"⚠️ An unexpected error occurred: {str(e)}"
            })

    return render(request, 'prompt_form.html')

@csrf_exempt
def order_summary_view(request):
    data = request.session.get('order_data')

    if not data:
        return HttpResponse("❌ No order data found.", status=400)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'edit':
            return render(request, 'manual_edit.html', data)

        elif action == 'confirm':
            try:
                customer_df = pd.read_csv(CUSTOMER_CSV)
                material_df = pd.read_csv(MATERIAL_CSV)

                if os.path.exists(SALESORDER_CSV):
                    sales_df = pd.read_csv(SALESORDER_CSV)
                else:
                    sales_df = pd.DataFrame(columns=[
                        'order_id', 'customer_number', 'customer_name', 'material_number', 'material_name',
                        'base_unit', 'quantity', 'net_weight', 'gross_weight', 'tax_percentage', 'tax_amount',
                        'standard_price', 'mrp', 'amount', 'total_price', 'currency', 'plant', 'storage_location',
                        'term_of_payment', 'discount', 'dunning_level', 'date'
                    ])

                customer_row = customer_df[customer_df['Customer_Number'].astype(str) == str(data['customer_number'])].iloc[0]
                material_row = material_df[material_df['Material Number'].astype(str) == str(data['material_number'])].iloc[0]

                # Calculations
                mrp = float(material_row['MRP'])
                quantity = int(data['quantity'])
                tax_percentage = float(material_row.get('tax', 0))

                amount = round(quantity * mrp, 2)
                tax_amount = round((amount * tax_percentage) / 100, 2)
                total_price = round(amount + tax_amount, 2)

                # Update stock
                material_df.loc[material_df['Material Number'].astype(str) == str(data['material_number']), 'stock'] -= quantity
                material_df.to_csv(MATERIAL_CSV, index=False)

                # Update customer predictions
                customer_df.loc[customer_df['Customer_Number'].astype(str) == str(data['customer_number']),
                                ['Terms_of_Payment', 'Discount_Percentage', 'Highest_Dunning_Level']] = [
                    data['term_of_payment'], data['discount'], data['dunning_level']
                ]
                customer_df.to_csv(CUSTOMER_CSV, index=False)

                new_order = {
                    'order_id': f"SO{len(sales_df)+1:04d}",
                    'customer_number': data['customer_number'],
                    'customer_name': customer_row.get('Customer_Name', ''),
                    'material_number': data['material_number'],
                    'material_name': material_row.get('Material Name', ''),
                    'base_unit': material_row.get('Base Unit of Measure', ''),
                    'quantity': quantity,
                    'net_weight': material_row.get('Net Weight', ''),
                    'gross_weight': material_row.get('Gross Weight', ''),
                    'tax_percentage': tax_percentage,
                    'tax_amount': tax_amount,
                    'standard_price': material_row.get('Standard Price', ''),
                    'mrp': mrp,
                    'amount': amount,
                    'total_price': total_price,
                    'currency': 'INR',
                    'plant': material_row.get('Plant', ''),
                    'storage_location': material_row.get('Storage Location', ''),
                    'term_of_payment': data['term_of_payment'],
                    'discount': data['discount'],
                    'dunning_level': data['dunning_level'],
                    'date': datetime.now().strftime('%Y-%m-%d')
                }

                # Save order
                sales_df = pd.concat([sales_df, pd.DataFrame([new_order])], ignore_index=True)
                sales_df.to_csv(SALESORDER_CSV, index=False)

                return render(request, 'order_summary.html', {
                    **data,
                    'amount': amount,
                    'tax_amount': tax_amount,
                    'total_price': total_price,
                    'success': "✅ Sales Order created successfully!"
                })

            except Exception as e:
                return render(request, 'order_summary.html', {
                    **data,
                    'error': f"⚠️ Failed to generate sales order: {str(e)}"
                })

    return render(request, 'order_summary.html', data)

@csrf_exempt
def manual_edit_view(request):
    data = request.session.get('order_data')

    if not data:
        return HttpResponse("❌ No order data found.", status=400)

    if request.method == 'GET':
        return render(request, 'manual_edit.html', data)

    elif request.method == 'POST':
        try:
            updated_data = {
                'customer_number': data['customer_number'],
                'material_number': data['material_number'],
                'quantity': data['quantity'],
                'term_of_payment': float(request.POST.get('term_of_payment')),
                'discount': float(request.POST.get('discount')),
                'dunning_level': int(request.POST.get('dunning_level')),
            }

            request.session['order_data'] = updated_data
            return redirect('order_summary')

        except Exception as e:
            return render(request, 'manual_edit.html', {
                **data,
                'error': f"⚠️ Failed to update manual values: {str(e)}"
            })

    return HttpResponse("❌ Invalid request method", status=405)

@csrf_exempt
def save_manual_values_view(request):
    if request.method == 'POST':
        try:
            context = {
                'customer_number': request.POST.get('customer_number'),
                'material_number': request.POST.get('material_number'),
                'quantity': int(request.POST.get('quantity')),
                'term_of_payment': float(request.POST.get('term_of_payment')),
                'discount': float(request.POST.get('discount')),
                'dunning_level': int(request.POST.get('dunning_level')),
            }

            request.session['order_data'] = context
            return redirect('order_summary')

        except Exception as e:
            return HttpResponse(f"⚠️ Error saving manual values: {str(e)}", status=400)

    return HttpResponse("❌ Invalid request method", status=405)

@csrf_exempt
def final_sales_order_view(request):
    try:
        # Load the latest order from salesorder.csv
        if os.path.exists(SALESORDER_CSV):
            df = pd.read_csv(SALESORDER_CSV)
            if df.empty:
                return HttpResponse("❌ No sales orders found.", status=404)

            latest_order = df.iloc[-1].to_dict()
            return render(request, 'final_sales_order.html', {'data': latest_order})
        else:
            return HttpResponse("❌ Sales order file not found.", status=404)

    except Exception as e:
        return HttpResponse(f"⚠️ Error loading final sales order: {str(e)}", status=500)

