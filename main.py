import os
from flask import Flask, flash, make_response, request, redirect, url_for, render_template, send_from_directory
from slugify import slugify

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(
  __name__,
  static_url_path='/',
  static_folder='./static',
)
app.config['TEMPLATES_AUTO_RELOAD'] = True
from discord_webhook import DiscordWebhook


@app.route('/favicon.ico')
def favicon():
  return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico',
                             mimetype='image/vnd.microsoft.icon')


@app.route("/game")
def game_page():
  locationId = request.args.get('location')
  path = f"./locations/{slugify(locationId)}.txt"
  recentArray = [
    file.split('/')[-1].replace('.txt', '')
    for file in sorted([
      './locations/' + file
      for file in os.listdir('./locations/') if file.endswith('.txt')
    ],
                       key=os.path.getmtime)[-3:]
  ]
  recentArray.reverse()
  if os.path.isfile(path):
    locationData = open(path, "rb").read().decode(
      "utf-8", errors="ignore").splitlines()  # you better fucking escape this
  else:
    return redirect(f"/create?location={locationId}", code=302)

  file_count = sum(len(files) for _, _, files in os.walk(r'./locations'))

  parsedData = []
  for line in locationData:
    if " -> " not in line:
      # simple <p>
      parsedData.append({"tag": "p", "text": line})
    else:
      firstArg = line.split(" -> ")[0]
      secondArg = line.split(" -> ")[1]
      if firstArg == "img":
        parsedData.append({"tag": "img", "src": f"{secondArg}"})
      elif firstArg == "key":
        thirdArg = line.split(" -> ")[2]
        parsedData.append({
          "tag": "key",
          "key": f"{secondArg}",
          "location": f"{thirdArg}"
        })
      else:
        # link
        parsedData.append({
          "tag": "a",
          "href": f"/game?location={secondArg}",
          "text": firstArg
        })
  return render_template("pages/game.jinja",
                         locationId=locationId,
                         placeData=parsedData,
                         fileCount=file_count,
                         recentArray=recentArray)


@app.route("/create")
def create_page():
  locationId = request.args.get('location')
  return render_template("pages/create.jinja", locationId=locationId)


@app.route("/edit")
def edit_page():
  locationId = request.args.get('location')
  path = f"./locations/{slugify(locationId)}.txt"
  if os.path.isfile(path):
    locationData = open(path).read()  # you better fucking escape this
  else:
    return redirect(f"/create?location={locationId}", code=302)
  return render_template("pages/edit.jinja",
                         locationId=locationId,
                         locationData=locationData)


@app.route("/createLocation", methods=['POST'])
def create_location_api():
  locationId = request.args.get('location')
  if "arrgh" in slugify(locationId):
    return redirect(f"/game?location={locationId}", code=302)
  f = open(f"./locations/{slugify(locationId)}.txt",
           "w")  # YOU BETTER FUCKING ESCAPE THIS
  f.write(request.form['content'].replace("\r\n\r\n", "\r\n").replace(
    "\r\n", "\n"))  # stupid double linebreak fix
  f.close()
  webhook = DiscordWebhook(
    url=
    'https://discord.com/api/webhooks/1084905932791758918/kKKtgIzoSRDSHj8nnr75pEhLzX01LgAkyr4mg2tG6ZyDL5ivvwzcQ4iGFwLUvLMlAfE4',
    content=f'Page changed: {slugify(locationId)}')
  webhook.execute()
  return redirect(f"/game?location={locationId}", code=302)


@app.route("/")
def redirect_to_start():
  return redirect("/game?location=start", code=301)


app.run(host='0.0.0.0', port=1234)
