# Ticket 03: Automated Unit Testing & Headless Verification

Type: task  
Status: resolved  
Blocked by: 01, 02  

## Question
How do we unit test the interactive wizard headlessly with mocked stdin (`unittest.mock.patch('builtins.input')`) and verify non-interactive fallback?

## Resolution
Added `test_interactive_wizard_with_mocked_inputs` to `TestOnDemandAndProjectInit` in `tests/test_skills_router.py`:
- Uses `unittest.mock.patch("builtins.input", side_effect=["2", "2"])` to simulate selecting custom profile and custom harnesses.
- Asserts that Claude/Gemini harnesses are installed while Cursor is omitted per selection.
- All 22 tests pass in 0.80s.
