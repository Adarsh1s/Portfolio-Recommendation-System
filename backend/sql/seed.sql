-- ============================================================
-- Portfolio Recommendation System - Complete Seed Data
-- ~230 rows across all reference tables
-- All Indian market instruments with illustrative return data
-- ============================================================

-- ============================================================
-- RISK PROFILES (4 rows)
-- ============================================================
INSERT INTO risk_profiles (profile_name, min_score, max_score, description) VALUES
('Conservative',          0,  25, 'Capital preservation focused. Minimal equity exposure, heavy debt and cash allocation. Suitable for short investment horizons and low risk appetite.'),
('Moderately Conservative', 26, 50, 'Balanced approach leaning defensive. Some equity for growth but majority in debt. Suitable for medium horizons with limited risk tolerance.'),
('Moderate',             51,  75, 'Balanced growth and stability. Significant equity allocation with debt cushion. Suitable for 5+ year horizons with moderate risk appetite.'),
('Aggressive',           76, 100, 'Maximum growth orientation. Heavy equity and international exposure. Suitable for 7+ year horizons with high risk tolerance.');

-- ============================================================
-- ASSET CLASSES (6 rows)
-- ============================================================
INSERT INTO asset_classes (name, description) VALUES
('Equity',        'Domestic equity instruments: large-cap, mid-cap, flexi-cap mutual funds and index ETFs'),
('Debt',          'Fixed income instruments: corporate bond funds, short duration debt funds, G-Secs'),
('Gold',          'Precious metal instruments: Gold ETFs and Sovereign Gold Bonds'),
('Cash & Liquid', 'High-liquidity low-risk instruments: liquid funds, overnight funds, money market'),
('International', 'Global equity exposure: US-focused funds, global diversified ETFs, Nasdaq ETFs'),
('Real Estate',   'REIT-based real estate exposure: office REITs, retail REITs listed on NSE/BSE');

-- ============================================================
-- PORTFOLIO MODELS (4 rows, one per risk profile)
-- ============================================================
INSERT INTO portfolio_models (model_name, risk_profile_id, description) VALUES
('Capital Shield',          1, 'Conservative model focused on capital preservation. 60% in debt, 20% equity via index funds, 10% gold, 10% liquid for emergencies.'),
('Steady Compounder',       2, 'Moderately conservative model balancing growth with safety. 40% equity, 40% debt, 10% gold, 10% cash.'),
('Balanced Growth',         3, 'Moderate growth model with diversified equity and debt. 60% equity across large/mid/flexi-cap, 25% debt, 10% gold, 5% cash.'),
('Alpha Maximiser',         4, 'Aggressive growth model targeting maximum long-term returns. 80% equity including international, 10% debt, 5% gold, 5% international.');

-- ============================================================
-- INSTRUMENTS (30 rows across all asset classes)
-- ============================================================
-- Equity instruments (asset_class_id = 1)
INSERT INTO instruments (name, ticker, asset_class_id, instrument_type, fund_house) VALUES
('Nifty 50 Index Fund - Direct',        'NIFTY50IDX',  1, 'Index Fund',   'UTI Mutual Fund'),
('Nifty Next 50 Index Fund - Direct',   'NIFTYNXT50',  1, 'Index Fund',   'UTI Mutual Fund'),
('Mirae Asset Large Cap Fund - Direct', 'MIRAELC',     1, 'Mutual Fund',  'Mirae Asset'),
('Parag Parikh Flexi Cap Fund - Direct','PPFCF',       1, 'Mutual Fund',  'PPFAS Mutual Fund'),
('HDFC Mid-Cap Opportunities Fund',     'HDFCMCAP',    1, 'Mutual Fund',  'HDFC Mutual Fund'),
('Kotak Emerging Equity Fund - Direct', 'KOTAKEMRG',   1, 'Mutual Fund',  'Kotak Mutual Fund'),
('Axis Small Cap Fund - Direct',        'AXISSML',     1, 'Mutual Fund',  'Axis Mutual Fund'),
('SBI Bluechip Fund - Direct',          'SBIBLUECHIP', 1, 'Mutual Fund',  'SBI Mutual Fund'),
('Nippon India Large Cap Fund',         'NIPPONLC',    1, 'Mutual Fund',  'Nippon India MF'),

-- Debt instruments (asset_class_id = 2)
('SBI Corporate Bond Fund - Direct',        'SBICORP',    2, 'Mutual Fund',  'SBI Mutual Fund'),
('HDFC Short Term Debt Fund - Direct',      'HDFCSTD',    2, 'Mutual Fund',  'HDFC Mutual Fund'),
('ICICI Pru Corporate Bond Fund - Direct',  'ICICPCORP',  2, 'Mutual Fund',  'ICICI Prudential'),
('Aditya Birla SL Corporate Bond Fund',     'ABSLCORP',   2, 'Mutual Fund',  'Aditya Birla SL'),
('Kotak Bond Short Term Fund - Direct',     'KOTAKBST',   2, 'Mutual Fund',  'Kotak Mutual Fund'),
('IDFC Government Securities Fund',         'IDFCGSEC',   2, 'G-Sec Fund',   'IDFC Mutual Fund'),

-- Gold instruments (asset_class_id = 3)
('Nippon India Gold ETF',                   'GOLDBEES',   3, 'ETF',          'Nippon India MF'),
('SBI Gold ETF',                            'SGOLD',      3, 'ETF',          'SBI Mutual Fund'),
('Sovereign Gold Bond 2026-Series IV',      'SGB2026',    3, 'Bond',         'Government of India'),
('HDFC Gold Fund - Direct',                 'HDFCGOLD',   3, 'Fund of Funds','HDFC Mutual Fund'),

-- Cash & Liquid instruments (asset_class_id = 4)
('Nippon India Liquid Fund - Direct',       'NIPPONLIQ',  4, 'Liquid Fund',  'Nippon India MF'),
('HDFC Liquid Fund - Direct',               'HDFCLIQ',    4, 'Liquid Fund',  'HDFC Mutual Fund'),
('Axis Overnight Fund - Direct',            'AXISONGHT',  4, 'Liquid Fund',  'Axis Mutual Fund'),

-- International instruments (asset_class_id = 5)
('Motilal Oswal Nasdaq 100 ETF',            'MON100',     5, 'ETF',          'Motilal Oswal MF'),
('Mirae Asset NYSE FANG+ ETF',              'MIRAEFANG',  5, 'ETF',          'Mirae Asset'),
('Parag Parikh Flexi Cap - Intl Portion',   'PPFCFINTL',  5, 'Mutual Fund',  'PPFAS Mutual Fund'),
('ICICI Pru US Bluechip Equity Fund',       'ICICPUSBC',  5, 'Fund of Funds','ICICI Prudential'),

-- Real Estate instruments (asset_class_id = 6)
('Embassy Office Parks REIT',               'EMBASSY',    6, 'REIT',         'Embassy Group'),
('Mindspace Business Parks REIT',           'MINDSPACE',  6, 'REIT',         'Mindspace REIT'),
('Brookfield India Real Estate Trust',      'BIRET',      6, 'REIT',         'Brookfield Asset Mgmt'),
('Nexus Select Trust REIT',                 'NEXUSREIT',  6, 'REIT',         'Nexus Malls');

-- ============================================================
-- PORTFOLIO ALLOCATIONS
-- Top-level asset class % per model (each model sums to 100%)
-- ============================================================

-- Model 1: Capital Shield (Conservative)
-- 20% Equity, 60% Debt, 10% Gold, 10% Cash
INSERT INTO portfolio_allocations (model_id, asset_class_id, allocation_percentage) VALUES
(1, 1, 20.00),  -- Equity
(1, 2, 60.00),  -- Debt
(1, 3, 10.00),  -- Gold
(1, 4, 10.00);  -- Cash & Liquid

-- Model 2: Steady Compounder (Moderately Conservative)
-- 40% Equity, 40% Debt, 10% Gold, 10% Cash
INSERT INTO portfolio_allocations (model_id, asset_class_id, allocation_percentage) VALUES
(2, 1, 40.00),  -- Equity
(2, 2, 40.00),  -- Debt
(2, 3, 10.00),  -- Gold
(2, 4, 10.00);  -- Cash & Liquid

-- Model 3: Balanced Growth (Moderate)
-- 60% Equity, 25% Debt, 10% Gold, 5% Cash
INSERT INTO portfolio_allocations (model_id, asset_class_id, allocation_percentage) VALUES
(3, 1, 60.00),  -- Equity
(3, 2, 25.00),  -- Debt
(3, 3, 10.00),  -- Gold
(3, 4, 5.00);   -- Cash & Liquid

-- Model 4: Alpha Maximiser (Aggressive)
-- 75% Equity, 10% Debt, 5% Gold, 5% Cash, 5% International
INSERT INTO portfolio_allocations (model_id, asset_class_id, allocation_percentage) VALUES
(4, 1, 75.00),  -- Equity
(4, 2, 10.00),  -- Debt
(4, 3, 5.00),   -- Gold
(4, 4, 5.00),   -- Cash & Liquid
(4, 5, 5.00);   -- International

-- ============================================================
-- SUB_ALLOCATION_TEMPLATES
-- One row per (model, asset_class) combination
-- ============================================================

-- Model 1: Capital Shield
INSERT INTO sub_allocation_templates (model_id, asset_class_id) VALUES
(1, 1),  -- template_id=1: Model1 Equity
(1, 2),  -- template_id=2: Model1 Debt
(1, 3),  -- template_id=3: Model1 Gold
(1, 4);  -- template_id=4: Model1 Cash

-- Model 2: Steady Compounder
INSERT INTO sub_allocation_templates (model_id, asset_class_id) VALUES
(2, 1),  -- template_id=5: Model2 Equity
(2, 2),  -- template_id=6: Model2 Debt
(2, 3),  -- template_id=7: Model2 Gold
(2, 4);  -- template_id=8: Model2 Cash

-- Model 3: Balanced Growth
INSERT INTO sub_allocation_templates (model_id, asset_class_id) VALUES
(3, 1),  -- template_id=9:  Model3 Equity
(3, 2),  -- template_id=10: Model3 Debt
(3, 3),  -- template_id=11: Model3 Gold
(3, 4);  -- template_id=12: Model3 Cash

-- Model 4: Alpha Maximiser
INSERT INTO sub_allocation_templates (model_id, asset_class_id) VALUES
(4, 1),  -- template_id=13: Model4 Equity
(4, 2),  -- template_id=14: Model4 Debt
(4, 3),  -- template_id=15: Model4 Gold
(4, 4),  -- template_id=16: Model4 Cash
(4, 5);  -- template_id=17: Model4 International

-- ============================================================
-- INSTRUMENT ALLOCATIONS
-- % of each instrument within its sub-allocation template
-- Each template must sum to 100%
-- ============================================================

-- Template 1: Model1 (Conservative) - Equity (index-heavy, safe)
-- Instruments: Nifty50(id=1), NiftyNxt50(id=2), Mirae LC(id=3)
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(1, 1, 60.00),  -- Nifty 50 Index Fund
(1, 2, 20.00),  -- Nifty Next 50
(1, 3, 20.00);  -- Mirae Asset Large Cap

-- Template 2: Model1 (Conservative) - Debt (safety first)
-- Instruments: SBI Corp(id=10), HDFC STD(id=11), ICICI Corp(id=12), ABSL Corp(id=13), IDFC GSec(id=15)
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(2, 10, 30.00),  -- SBI Corporate Bond
(2, 11, 25.00),  -- HDFC Short Term Debt
(2, 12, 20.00),  -- ICICI Pru Corporate Bond
(2, 13, 15.00),  -- Aditya Birla SL Corporate Bond
(2, 15, 10.00);  -- IDFC Govt Securities

-- Template 3: Model1 (Conservative) - Gold
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(3, 16, 50.00),  -- Nippon India Gold ETF
(3, 18, 50.00);  -- Sovereign Gold Bond 2026

-- Template 4: Model1 (Conservative) - Cash
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(4, 20, 60.00),  -- Nippon India Liquid
(4, 21, 40.00);  -- HDFC Liquid Fund

-- Template 5: Model2 (Mod Conservative) - Equity
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(5, 1,  40.00),  -- Nifty 50 Index Fund
(5, 4,  30.00),  -- Parag Parikh Flexi Cap
(5, 3,  20.00),  -- Mirae Asset Large Cap
(5, 5,  10.00);  -- HDFC Mid-Cap Opportunities

-- Template 6: Model2 (Mod Conservative) - Debt
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(6, 10, 35.00),  -- SBI Corporate Bond
(6, 11, 30.00),  -- HDFC Short Term Debt
(6, 14, 20.00),  -- Kotak Bond Short Term
(6, 15, 15.00);  -- IDFC Govt Securities

-- Template 7: Model2 (Mod Conservative) - Gold
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(7, 16, 50.00),  -- Nippon India Gold ETF
(7, 17, 30.00),  -- SBI Gold ETF
(7, 18, 20.00);  -- Sovereign Gold Bond 2026

-- Template 8: Model2 (Mod Conservative) - Cash
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(8, 20, 50.00),  -- Nippon India Liquid
(8, 22, 50.00);  -- Axis Overnight Fund

-- Template 9: Model3 (Moderate) - Equity (broader diversification)
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(9, 1,  30.00),  -- Nifty 50 Index Fund
(9, 4,  25.00),  -- Parag Parikh Flexi Cap
(9, 5,  20.00),  -- HDFC Mid-Cap Opportunities
(9, 6,  15.00),  -- Kotak Emerging Equity
(9, 8,  10.00);  -- SBI Bluechip Fund

-- Template 10: Model3 (Moderate) - Debt
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(10, 10, 40.00),  -- SBI Corporate Bond
(10, 11, 35.00),  -- HDFC Short Term Debt
(10, 12, 25.00);  -- ICICI Pru Corporate Bond

-- Template 11: Model3 (Moderate) - Gold
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(11, 16, 50.00),  -- Nippon India Gold ETF
(11, 19, 30.00),  -- HDFC Gold Fund
(11, 18, 20.00);  -- Sovereign Gold Bond 2026

-- Template 12: Model3 (Moderate) - Cash
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(12, 20, 60.00),  -- Nippon India Liquid
(12, 21, 40.00);  -- HDFC Liquid Fund

-- Template 13: Model4 (Aggressive) - Equity (multi-cap, growth)
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(13, 4,  25.00),  -- Parag Parikh Flexi Cap
(13, 5,  20.00),  -- HDFC Mid-Cap Opportunities
(13, 6,  20.00),  -- Kotak Emerging Equity
(13, 7,  15.00),  -- Axis Small Cap
(13, 1,  10.00),  -- Nifty 50 Index Fund
(13, 9,  10.00);  -- Nippon India Large Cap

-- Template 14: Model4 (Aggressive) - Debt (minimal, for liquidity buffer)
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(14, 11, 60.00),  -- HDFC Short Term Debt
(14, 14, 40.00);  -- Kotak Bond Short Term

-- Template 15: Model4 (Aggressive) - Gold
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(15, 16, 60.00),  -- Nippon India Gold ETF
(15, 18, 40.00);  -- Sovereign Gold Bond 2026

-- Template 16: Model4 (Aggressive) - Cash
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(16, 22, 60.00),  -- Axis Overnight Fund
(16, 20, 40.00);  -- Nippon India Liquid

-- Template 17: Model4 (Aggressive) - International
INSERT INTO instrument_allocations (template_id, instrument_id, allocation_percentage) VALUES
(17, 23, 40.00),  -- Motilal Oswal Nasdaq 100 ETF
(17, 24, 30.00),  -- Mirae Asset NYSE FANG+
(17, 26, 30.00);  -- ICICI Pru US Bluechip

-- ============================================================
-- INSTRUMENT RETURNS (90 rows: 30 instruments × 3 periods)
-- Illustrative mock return data for Indian market instruments
-- ============================================================
INSERT INTO instrument_returns (instrument_id, period, return_percentage) VALUES
-- Nifty 50 Index Fund
(1,  '1Y', 12.40),  (1,  '3Y', 14.80),  (1,  '5Y', 13.20),
-- Nifty Next 50 Index Fund
(2,  '1Y', 15.20),  (2,  '3Y', 17.40),  (2,  '5Y', 14.90),
-- Mirae Asset Large Cap
(3,  '1Y', 13.80),  (3,  '3Y', 16.20),  (3,  '5Y', 14.10),
-- Parag Parikh Flexi Cap
(4,  '1Y', 18.50),  (4,  '3Y', 20.30),  (4,  '5Y', 19.80),
-- HDFC Mid-Cap Opportunities
(5,  '1Y', 22.10),  (5,  '3Y', 24.60),  (5,  '5Y', 21.30),
-- Kotak Emerging Equity
(6,  '1Y', 24.80),  (6,  '3Y', 26.40),  (6,  '5Y', 23.10),
-- Axis Small Cap
(7,  '1Y', 28.30),  (7,  '3Y', 30.10),  (7,  '5Y', 27.60),
-- SBI Bluechip
(8,  '1Y', 12.90),  (8,  '3Y', 15.40),  (8,  '5Y', 13.80),
-- Nippon India Large Cap
(9,  '1Y', 14.20),  (9,  '3Y', 16.80),  (9,  '5Y', 14.50),

-- Debt instruments
-- SBI Corporate Bond
(10, '1Y', 7.60),   (10, '3Y', 8.20),   (10, '5Y', 7.90),
-- HDFC Short Term Debt
(11, '1Y', 7.10),   (11, '3Y', 7.80),   (11, '5Y', 7.50),
-- ICICI Pru Corporate Bond
(12, '1Y', 7.80),   (12, '3Y', 8.40),   (12, '5Y', 8.00),
-- Aditya Birla SL Corporate Bond
(13, '1Y', 7.40),   (13, '3Y', 8.10),   (13, '5Y', 7.70),
-- Kotak Bond Short Term
(14, '1Y', 6.90),   (14, '3Y', 7.60),   (14, '5Y', 7.20),
-- IDFC Govt Securities
(15, '1Y', 6.50),   (15, '3Y', 7.20),   (15, '5Y', 6.80),

-- Gold instruments
-- Nippon India Gold ETF
(16, '1Y', 11.30),  (16, '3Y', 9.80),   (16, '5Y', 10.40),
-- SBI Gold ETF
(17, '1Y', 11.10),  (17, '3Y', 9.60),   (17, '5Y', 10.20),
-- Sovereign Gold Bond 2026
(18, '1Y', 13.30),  (18, '3Y', 11.80),  (18, '5Y', 12.40),
-- HDFC Gold Fund
(19, '1Y', 10.90),  (19, '3Y', 9.50),   (19, '5Y', 10.00),

-- Liquid instruments
-- Nippon India Liquid Fund
(20, '1Y', 6.80),   (20, '3Y', 6.20),   (20, '5Y', 6.00),
-- HDFC Liquid Fund
(21, '1Y', 6.75),   (21, '3Y', 6.15),   (21, '5Y', 5.95),
-- Axis Overnight Fund
(22, '1Y', 6.60),   (22, '3Y', 6.00),   (22, '5Y', 5.80),

-- International instruments
-- Motilal Oswal Nasdaq 100
(23, '1Y', 28.40),  (23, '3Y', 22.60),  (23, '5Y', 24.80),
-- Mirae Asset NYSE FANG+
(24, '1Y', 32.10),  (24, '3Y', 25.40),  (24, '5Y', 28.20),
-- Parag Parikh Flexi Cap Intl
(25, '1Y', 16.30),  (25, '3Y', 18.90),  (25, '5Y', 17.40),
-- ICICI Pru US Bluechip
(26, '1Y', 24.60),  (26, '3Y', 20.30),  (26, '5Y', 22.10),

-- REIT instruments
-- Embassy Office Parks
(27, '1Y', 8.40),   (27, '3Y', 10.20),  (27, '5Y', 9.60),
-- Mindspace Business Parks
(28, '1Y', 9.10),   (28, '3Y', 10.80),  (28, '5Y', 10.00),
-- Brookfield India REIT
(29, '1Y', 7.80),   (29, '3Y', 9.60),   (29, '5Y', 8.90),
-- Nexus Select Trust
(30, '1Y', 10.20),  (30, '3Y', 11.40),  (30, '5Y', 10.70);


-- ============================================================
-- MOCK USERS (To make the app feel real)
-- Password for all users is: password123
-- ============================================================
INSERT INTO users (user_id, name, email, password_hash) VALUES
(1001, 'Ravi Desai', 'ravi@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1002, 'Priya Sharma', 'priya@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1003, 'Karan Kapoor', 'karan@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1004, 'Amitabh Singh', 'amitabh@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK'),
(1005, 'Neha Gupta', 'neha@example.com', '$2b$12$C/CYNVPmhv6qMFybq3Ozquk1iy10JOSBR/nwx0sbuPjFAidIvYniK')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_profiles (user_id, monthly_income, monthly_expenses, investment_amount, investment_horizon_years, investment_goal, risk_score, risk_profile_id) VALUES
(1001, 150000, 50000, 1000000, 3, 'Save for wedding', 20, 1),
(1002, 350000, 100000, 2500000, 10, 'Early Retirement', 85, 4),
(1003, 100000, 40000, 500000, 5, 'Buy a house', 60, 3),
(1004, 200000, 80000, 1500000, 7, 'Child Education', 45, 2),
(1005, 500000, 200000, 5000000, 15, 'Wealth Creation', 90, 4)
ON CONFLICT (user_id) DO NOTHING;

-- Log the profile creation
INSERT INTO audit_log (user_id, action, metadata) VALUES
(1001, 'RISK_SCORE_UPDATED', '{"new_risk_score": 20}'),
(1002, 'RISK_SCORE_UPDATED', '{"new_risk_score": 85}'),
(1003, 'RISK_SCORE_UPDATED', '{"new_risk_score": 60}'),
(1004, 'RISK_SCORE_UPDATED', '{"new_risk_score": 45}'),
(1005, 'RISK_SCORE_UPDATED', '{"new_risk_score": 90}');
