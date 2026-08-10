from pathlib import Path
import zipfile

from indd2docx.idml.package import IDMLPackage
from indd2docx.idml.parser import IDMLParser


def make_fixture(path: Path):
    designmap = '''<Document StoryList="s1 s2"><Story src="Stories/Story_s1.xml"/><Story src="Stories/Story_s2.xml"/><Spread src="Spreads/Spread_u1.xml"/></Document>'''
    story1 = '''<Story xmlns="http://ns.adobe.com/InDesign/4.0/"><ParagraphStyleRange AppliedParagraphStyle="ParagraphStyle/$ID/Body"><CharacterStyleRange AppliedFont="Arial" PointSize="12"><Content>Hello </Content></CharacterStyleRange><CharacterStyleRange AppliedFont="Arial" PointSize="12" FontStyle="Bold"><Content>world</Content></CharacterStyleRange></ParagraphStyleRange><Table ColumnCount="2"><Row Height="20"><Cell TopEdgeStrokeWeight="0" TopEdgeStrokeColor="None"><ParagraphStyleRange><CharacterStyleRange><Content>A</Content></CharacterStyleRange></ParagraphStyleRange></Cell><Cell TopEdgeStrokeWeight="1" TopEdgeStrokeColor="Black"><ParagraphStyleRange><CharacterStyleRange><Content>B</Content></CharacterStyleRange></ParagraphStyleRange></Cell></Row></Table></Story>'''
    story2 = '''<Story xmlns="http://ns.adobe.com/InDesign/4.0/"><ParagraphStyleRange><CharacterStyleRange><Content>Second story</Content></CharacterStyleRange></ParagraphStyleRange></Story>'''
    spread = '''<Spread><Page Self="page1" Name="1" GeometricBounds="0 0 792 612"/><TextFrame Self="tf1" ParentStory="s1" ParentPage="page1" GeometricBounds="10 20 100 300"/></Spread>'''
    container = '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"/>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("designmap.xml", designmap)
        z.writestr("META-INF/container.xml", container)
        z.writestr("Stories/Story_s1.xml", story1)
        z.writestr("Stories/Story_s2.xml", story2)
        z.writestr("Spreads/Spread_u1.xml", spread)


def test_parser_builds_independent_model(tmp_path):
    idml = tmp_path / "sample.idml"
    make_fixture(idml)
    root = IDMLPackage(idml, tmp_path / "work").extract()
    model = IDMLParser(root).parse("sample")

    assert model.name == "sample"
    assert [s.id for s in model.stories] == ["s1", "s2"]
    assert model.stories[0].paragraphs[0].text == "Hello world"
    assert model.stories[0].paragraphs[0].runs[1].character.bold is True
    assert model.stories[0].tables[0].column_count == 2
    assert model.stories[0].tables[0].rows[0].cells[1].borders["top"].visible
    assert not model.stories[0].tables[0].rows[0].cells[0].borders["top"].visible
    assert model.pages[0].width_pt == 612
    assert model.pages[0].height_pt == 792
    assert model.stories[0].text_frames[0].id == "tf1"
