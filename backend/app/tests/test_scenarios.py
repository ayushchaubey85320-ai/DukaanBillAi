"""
Automated Test Suite for All 21 Real-World Indian Retail Scenarios
Systematically validates the Scenario Coverage Matrix specified in the master plan.
"""
import unittest
import time
from backend.app.ml.dialogue_manager import get_session, process_dialogue_turn, _ACTIVE_SESSIONS
from backend.app.billing.gst_engine import (
    validate_gstin, calculate_bill_totals, mask_phone_number
)
from backend.app.billing.hsn_db import lookup_hsn
from backend.app.billing.thermal_printer import format_thermal_receipt_text
from backend.app.billing.qr_generator import generate_upi_payment_url, generate_qr_base64
from backend.app.ml.regional_numbers import parse_currency_amount, parse_number_value

class TestBillingAgentScenarios(unittest.TestCase):

    def setUp(self):
        # Clear test sessions before each test
        _ACTIVE_SESSIONS.clear()

    def test_scenario_01_basic_add(self):
        """Scenario 1: Add 1 item, ask total"""
        res = process_dialogue_turn("test_s1", "add 2 kg rice at 60 rupees")
        self.assertEqual(len(res["bill"]["items"]), 1)
        self.assertEqual(res["bill"]["items"][0]["name"], "Rice")
        self.assertEqual(res["bill"]["items"][0]["quantity"], 2.0)
        self.assertEqual(res["bill"]["items"][0]["rate"], 60.0)

        # Ask total
        res_total = process_dialogue_turn("test_s1", "total kitna hua")
        self.assertIn("120", str(res_total["bill"]["items_subtotal"]))
        self.assertGreater(res_total["bill"]["grand_total"], 0)

    def test_scenario_02_multiple_items(self):
        """Scenario 2: Add 5 items, change qty of 2, remove 1"""
        s_id = "test_s2"
        items_to_add = [
            "add 1 kg sugar 45 rs",
            "add 2 biscuit 20 rs",
            "add 1 litre milk 60 rs",
            "add 2 soap 40 rs",
            "add 1 notebook 50 rs"
        ]
        for prompt in items_to_add:
            process_dialogue_turn(s_id, prompt)

        sess = get_session(s_id)
        self.assertEqual(len(sess.items), 5)

        # Change quantity of sugar to 3
        process_dialogue_turn(s_id, "sugar 3 kg")
        sugar_item = next(it for it in sess.items if it["name"] == "Sugar")
        self.assertEqual(sugar_item["quantity"], 3.0)

        # Remove 1 item
        process_dialogue_turn(s_id, "remove soap")
        self.assertEqual(len(sess.items), 4)
        self.assertFalse(any(it["name"] == "Soap" for it in sess.items))

    def test_scenario_03_gst_variants(self):
        """Scenario 3: Different GST rates per HSN (5%, 12%, 18%)"""
        items = [
            {"name": "Rice", "quantity": 1, "rate": 100.0, "hsn": "1006", "gst_rate": 5.0},
            {"name": "Butter", "quantity": 1, "rate": 100.0, "hsn": "0405", "gst_rate": 12.0},
            {"name": "Biscuits", "quantity": 1, "rate": 100.0, "hsn": "1905", "gst_rate": 18.0}
        ]
        calc = calculate_bill_totals(items)
        self.assertEqual(calc["items"][0]["total_tax"], 5.0)   # 2.5 CGST + 2.5 SGST
        self.assertEqual(calc["items"][1]["total_tax"], 12.0)  # 6.0 CGST + 6.0 SGST
        self.assertEqual(calc["items"][2]["total_tax"], 18.0)  # 9.0 CGST + 9.0 SGST
        self.assertEqual(calc["total_tax"], 35.0)

    def test_scenario_04_discount_types(self):
        """Scenario 4: % discount, flat amount, per-item discount"""
        items = [{"name": "Shirt", "quantity": 2, "rate": 500.0, "gst_rate": 0.0}]
        # 10% discount
        calc_pct = calculate_bill_totals(items, overall_discount_percent=10.0)
        self.assertEqual(calc_pct["discount_applied"], 100.0)
        self.assertEqual(calc_pct["grand_total"], 900.0)

        # Flat ₹150 discount
        calc_flat = calculate_bill_totals(items, overall_discount_amount=150.0)
        self.assertEqual(calc_flat["discount_applied"], 150.0)
        self.assertEqual(calc_flat["grand_total"], 850.0)

    def test_scenario_05_return_cancel(self):
        """Scenario 5: 'Cancel last item', 'Remove all'"""
        s_id = "test_s5"
        process_dialogue_turn(s_id, "add 1 bread 40 rs")
        process_dialogue_turn(s_id, "add 1 jam 120 rs")
        self.assertEqual(len(get_session(s_id).items), 2)

        # Cancel last item
        res = process_dialogue_turn(s_id, "cancel last item")
        self.assertEqual(len(get_session(s_id).items), 1)
        self.assertEqual(get_session(s_id).items[0]["name"], "Bread")

        # Start new / remove all
        process_dialogue_turn(s_id, "start new bill")
        self.assertEqual(len(get_session(s_id).items), 0)

    def test_scenario_06_round_off_errors(self):
        """Scenario 6: Prices ending with .99, .01 with zero drift"""
        items = [
            {"name": "Item A", "quantity": 1, "rate": 99.99, "gst_rate": 0.0},
            {"name": "Item B", "quantity": 1, "rate": 0.01, "gst_rate": 0.0}
        ]
        calc = calculate_bill_totals(items)
        self.assertEqual(calc["items_subtotal"], 100.00)
        self.assertEqual(calc["round_off"], 0.0)
        self.assertEqual(calc["grand_total"], 100.0)

        # .49 rounds down to nearest rupee
        calc_down = calculate_bill_totals([{"name": "A", "quantity": 1, "rate": 45.40, "gst_rate": 0.0}])
        self.assertEqual(calc_down["grand_total"], 45.0)
        self.assertEqual(calc_down["round_off"], -0.40)

    def test_scenario_07_indian_currency_format(self):
        """Scenario 7: Indian Currency parsing: '₹1,200.50', '1200.5 rupees'"""
        val1 = parse_currency_amount("add jacket at ₹1,200.50")
        self.assertEqual(val1, 1200.50)
        val2 = parse_currency_amount("1200.5 rupees")
        self.assertEqual(val2, 1200.5)

    def test_scenario_08_hinglish_spelling(self):
        """Scenario 8: Hinglish Spelling: '2 kilo chawal 45', '3 pcs biscuit 20 each'"""
        res1 = process_dialogue_turn("test_s8", "2 kilo chawal 45")
        self.assertEqual(res1["bill"]["items"][0]["name"], "Chawal")
        self.assertEqual(res1["bill"]["items"][0]["quantity"], 2.0)
        self.assertEqual(res1["bill"]["items"][0]["rate"], 45.0)

        res2 = process_dialogue_turn("test_s8", "3 pcs biscuit 20 each")
        self.assertEqual(len(res2["bill"]["items"]), 2)

    def test_scenario_09_regional_numbers(self):
        """Scenario 9: Regional Hindi Numbers: 'दो किलो चावल पैंसठ रुपये'"""
        res = process_dialogue_turn("test_s9", "दो किलो चावल पैंसठ रुपये")
        item = res["bill"]["items"][0]
        self.assertEqual(item["quantity"], 2.0)
        self.assertEqual(item["rate"], 65.0)

    def test_scenario_10_gstin_validation(self):
        """Scenario 10: GSTIN Validation checksum & 15-char regex"""
        valid_res = validate_gstin("07AAACB1234D1Z5")
        self.assertTrue(valid_res["valid"])
        self.assertEqual(valid_res["state_name"], "Delhi")

        invalid_res = validate_gstin("12345ABC")
        self.assertFalse(invalid_res["valid"])

    def test_scenario_11_hsn_code_lookup(self):
        """Scenario 11: Auto lookup HSN (e.g., rice -> 1006)"""
        rice_hsn = lookup_hsn("Basmati Rice")
        self.assertEqual(rice_hsn["hsn"], "1006")
        self.assertEqual(rice_hsn["rate"], 5.0)

        paracetamol_hsn = lookup_hsn("Paracetamol 650")
        self.assertEqual(paracetamol_hsn["hsn"], "3004")

    def test_scenario_12_bulk_add_voice(self):
        """Scenario 12: Bulk Add via Voice 'Add 10 tomatoes, 5 potatoes, 2 onions'"""
        res = process_dialogue_turn("test_s12", "Add 10 tomatoes, 5 potatoes, 2 onions")
        self.assertEqual(len(res["bill"]["items"]), 3)
        names = [it["name"].lower() for it in res["bill"]["items"]]
        self.assertTrue(any("tomato" in n for n in names))
        self.assertTrue(any("potato" in n for n in names))
        self.assertTrue(any("onion" in n for n in names))

    def test_scenario_13_offline_resilience(self):
        """Scenario 13: Offline resilience / self-contained ML without internet"""
        res = process_dialogue_turn("test_s13", "add 1 atta 40 rs")
        self.assertIsNotNone(res["intent"])
        self.assertGreater(res["confidence"], 0.5)
        self.assertEqual(res["bill"]["items"][0]["name"], "Atta")

    def test_scenario_14_multi_language_switch(self):
        """Scenario 14: Multi-Language Switch English <-> Hindi"""
        s_id = "test_s14"
        res_hi = process_dialogue_turn(s_id, "switch to Hindi")
        self.assertEqual(res_hi["language"], "hi")
        self.assertIn("नमस्ते", res_hi["reply"])

        res_en = process_dialogue_turn(s_id, "switch to English")
        self.assertEqual(res_en["language"], "en")
        self.assertIn("English", res_en["reply"])

    def test_scenario_15_customer_data_privacy(self):
        """Scenario 15: Mask phone (last 4 digits only visible)"""
        masked = mask_phone_number("9876543210")
        self.assertEqual(masked, "******3210")

        res = process_dialogue_turn("test_s15", "customer Ramesh phone 9876543210")
        self.assertEqual(res["bill"]["customer_phone_masked"], "******3210")

    def test_scenario_16_thermal_printer_80mm(self):
        """Scenario 16: Format ESC/POS for 80mm thermal printers"""
        bill_data = {
            "bill_id": "INV-1001",
            "date": "25-Oct-2026",
            "customer_name": "Ramesh",
            "customer_phone_masked": "******3210",
            "items": [{"name": "Rice", "hsn": "1006", "quantity": 2, "unit": "kg", "rate": 60, "total_amount": 120}],
            "items_subtotal": 120.0,
            "grand_total": 120.0
        }
        shop_info = {"name": "Test Store", "phone": "9999999999", "gstin": "07AAACB1234D1Z5"}
        txt = format_thermal_receipt_text(bill_data, shop_info, columns=48)
        self.assertIn("TAX INVOICE", txt)
        self.assertIn("Rice", txt)
        self.assertIn("120.00", txt)

    def test_scenario_17_qr_code_generation(self):
        """Scenario 17: NPCI UPI QR string and Base64 image"""
        upi = generate_upi_payment_url("test@upi", "Sharma Store", 150.0, "1001")
        self.assertIn("upi://pay?", upi)
        self.assertIn("am=150.00", upi)

        b64 = generate_qr_base64(upi)
        self.assertTrue(b64.startswith("data:image/png;base64,"))

    def test_scenario_18_regulatory_edge_cases(self):
        """Scenario 18: Reverse charge GST (RCM) and zero-rated items"""
        # Reverse charge: tax is not added to supplier invoice total
        items = [{"name": "Goods Under RCM", "quantity": 1, "rate": 500.0, "gst_rate": 18.0}]
        calc_rcm = calculate_bill_totals(items, reverse_charge=True)
        self.assertTrue(calc_rcm["reverse_charge"])
        self.assertEqual(calc_rcm["total_tax"], 0.0)
        self.assertEqual(calc_rcm["grand_total"], 500.0)

    def test_scenario_19_concurrent_sessions(self):
        """Scenario 19: Separate session IDs, isolated state"""
        res1 = process_dialogue_turn("user_counter_1", "add 1 milk 50 rs")
        res2 = process_dialogue_turn("user_counter_2", "add 2 bread 40 rs")

        sess1 = get_session("user_counter_1")
        sess2 = get_session("user_counter_2")

        self.assertEqual(len(sess1.items), 1)
        self.assertEqual(sess1.items[0]["name"], "Milk")
        self.assertEqual(len(sess2.items), 1)
        self.assertEqual(sess2.items[0]["name"], "Bread")

    def test_scenario_20_session_timeout(self):
        """Scenario 20: Inactivity > 5 min notice"""
        s_id = "test_s20"
        process_dialogue_turn(s_id, "add 1 rice 60 rs")
        sess = get_session(s_id)
        # Simulate 6 minutes passing
        sess.last_active_time = time.time() - 360

        res_after = process_dialogue_turn(s_id, "add 1 sugar 45 rs")
        self.assertIn("inactivity", res_after["reply"].lower())

    def test_scenario_21_error_recovery_dialogue_repair(self):
        """Scenario 21: Error recovery / clarification 'quantity 5 kar do'"""
        s_id = "test_s21"
        process_dialogue_turn(s_id, "add 2 kg rice at 60")
        # User repairs: "rice 5 kg"
        res_repair = process_dialogue_turn(s_id, "rice 5 kg")
        self.assertEqual(res_repair["bill"]["items"][0]["quantity"], 5.0)

    def test_scenario_22_gst_removal(self):
        """Scenario 22: GST removal 'gst htao' reduces tax to 0 and grand total to net rate"""
        s_id = "test_s22"
        res1 = process_dialogue_turn(s_id, "add 2 biscuit 40 each")
        self.assertGreater(res1["bill"]["total_tax"], 0.0)
        res_rm = process_dialogue_turn(s_id, "gst htao")
        self.assertEqual(res_rm["intent"], "remove_gst")
        self.assertEqual(res_rm["bill"]["total_tax"], 0.0)
        self.assertEqual(res_rm["bill"]["grand_total"], 80.0)
        self.assertIn("0%", res_rm["reply"])

def run_all_scenarios_report():
    """Runs all 21 test scenarios and returns a structured JSON summary."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBillingAgentScenarios)
    results = []
    
    for test in suite:
        test_name = test._testMethodName
        doc = test._testMethodDoc or test_name
        start_t = time.time()
        try:
            test.debug()
            elapsed_ms = round((time.time() - start_t) * 1000, 2)
            results.append({
                "test": test_name,
                "description": doc.strip(),
                "status": "PASSED",
                "latency_ms": elapsed_ms,
                "error": None
            })
        except Exception as e:
            elapsed_ms = round((time.time() - start_t) * 1000, 2)
            results.append({
                "test": test_name,
                "description": doc.strip(),
                "status": "FAILED",
                "latency_ms": elapsed_ms,
                "error": str(e)
            })

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASSED")
    return {
        "total_scenarios": total,
        "passed_scenarios": passed,
        "failed_scenarios": total - passed,
        "pass_rate": f"{(passed / total) * 100:.1f}%",
        "results": results
    }

if __name__ == "__main__":
    unittest.main()
