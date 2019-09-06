import urllib.request
import bs4
from database import DataBase

URL = "https://www.dota2.com/patches/"

DB = DataBase('data.sql')

raw_content = urllib.request.urlopen(URL)
content = raw_content.read().decode('utf8')

raw_content.close()

schema = bs4.BeautifulSoup(content, 'html.parser')

raw_patches = schema.find(id="PatchSelector")
patches = list()
for patch in raw_patches:
  if isinstance(patch, bs4.element.NavigableString):
    continue
  if patch.text[0].isdigit():
    patches.append(patch.text)
    DB.add_patch(patch.text)
print(f"Found patches: {patches}")

#patches = ['7.22']

for patch in patches:
  raw_content = urllib.request.urlopen(URL + patch)
  content = raw_content.read().decode('utf8')
  raw_content.close()
  schema = bs4.BeautifulSoup(content, 'html.parser')

  # hero updates
  for hero in schema.findAll('div', {"class": 'HeroNotes'}):
      hero_name = hero.select('.HeroName')[0].get_text()
      DB.add_hero(hero_name)
      patch_notes = list()
      common_notes =  hero.find('ul', {"class": 'HeroNotesList'})
      if common_notes is not None:
        for note in common_notes.findChildren("li", recursive=False):
          patch_notes.append(note.text)
          DB.add_hero_changes(
              change_type='common',
              patch=patch,
              hero=hero_name,
              info=note.text)
      ability_notes = dict()
      for ability in hero.findAll('div', {"class": 'HeroAbilityNotes'}):
        ability_name = ability.select('.AbilityName')[0].text
        ability_notes[ability_name] = list()
        for note in ability.findAll('li', {"class": 'PatchNote'}):
          ability_notes[ability_name].append(note.text)
          DB.add_hero_changes(
              change_type='ability',
              patch=patch,
              hero=hero_name,
              info=note.text,
              meta=ability_name)
      talent_notes = list()
      talents = hero.find('div', {"class": 'TalentNotes'})
      if talents is not None:
        for talent in talents.findAll('li'):
          talent_notes.append(talent.text)
          DB.add_hero_changes(
              change_type='talent',
              patch=patch,
              hero=hero_name,
              info=talent.text)

  # item updates
  item_notes = dict()
  for item in schema.findAll('div', {"class": 'ItemNotes'}):
      item_name = item.select('.ItemName')[0].get_text()
      DB.add_item(item_name)
      item_notes[item_name] = list()
      for note in item.findAll('li', {"class": 'PatchNote'}):
        item_notes[item_name].append(note.text)
        DB.add_item_changes(
            patch=patch,
            item=item_name,
            info=note.text)

  # general updates
  general =  schema.find(id='GeneralSection')
  print(general)
  if general is not None:
      for note in general.findAll('li', {"class": 'PatchNote'}):
        DB.add_general_changes(
            patch=patch,
            info=note.text)
