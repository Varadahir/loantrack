CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    borrower_name TEXT NOT NULL,
    loan_amount NUMERIC(14, 2) NOT NULL,
    property_city TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);