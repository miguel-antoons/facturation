import { Route, Routes } from "react-router-dom";

import BillingList from "@/pages/billingList";
import Billing from "@/pages/billing";
import CustomerList from "@/pages/customerList";
import Customer from "@/pages/customer";
import Home from "@/pages/home.tsx";
import CreditNoteList from "@/pages/creditNoteList.tsx";
import CreditNote from "@/pages/creditNote.tsx";

function App() {
  return (
    <Routes>
      <Route element={<Home />} path="/" />
      <Route element={<BillingList />} path="/billlist" />
      <Route element={<Billing />} path="/bill/:id" />
      <Route element={<CustomerList />} path="/customerlist" />
      <Route element={<Customer />} path="/customer/:id" />
      <Route element={<CreditNoteList />} path="/cnotelist" />
      <Route element={<CreditNote />} path="/cnote/:id" />
    </Routes>
  );
}

export default App;
