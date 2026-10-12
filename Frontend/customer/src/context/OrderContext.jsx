import { createContext, useContext, useState } from "react";
import { v4 as uuid } from "uuid";

const OrderContext = createContext();

export const OrderProvider = ({ children }) => {
  const [orders, setOrders] = useState(
    JSON.parse(localStorage.getItem("orders")) || []
  );

  const addOrder = (items, email) => {
    const order = {
      order_id: `ORD-${uuid().slice(0, 6)}`,
      items,
      email,
      date: new Date().toISOString(),
    };

    const updated = [...orders, order];
    setOrders(updated);
    localStorage.setItem("orders", JSON.stringify(updated));
  };

  return (
    <OrderContext.Provider value={{ orders, addOrder }}>
      {children}
    </OrderContext.Provider>
  );
};

export const useOrders = () => useContext(OrderContext);
