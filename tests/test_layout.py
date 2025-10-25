from src.domain.layout import parse_layout_dsl


def test_parse_layout_defaults():
    spec = parse_layout_dsl(None)
    assert spec.columns == ["Date", "Provider", "Reason", "Ref"]
    assert spec.sort_by[0][0] == "Date"


def test_parse_layout_custom_and_unknown():
    spec = parse_layout_dsl(
        "columns=Date|Facility|Foo|Summary; sort=Provider desc; group_by=Facility"
    )
    assert spec.columns == ["Date", "Facility", "Summary"]
    assert "Foo" in spec.unknown_columns
    assert spec.group_by == "Facility"
