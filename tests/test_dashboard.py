from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).parents[1]

def test_dashboard_default_and_empty_filter():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    assert not app.exception
    assert len(app.metric)==4
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any('Choose at least' in x.value for x in app.warning)


def test_dashboard_capacity_and_cost_change_metrics():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=30)
    before=app.metric[3].value
    app.number_input[0].set_value(10000.0).run()
    assert not app.exception and app.metric[3].value != before
    app.slider[0].set_value(2.0).run()
    assert not app.exception
