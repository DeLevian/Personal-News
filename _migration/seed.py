"""One-time v2 configuration migration on the dedicated branch only."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(path,data):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
rows='''openai|OpenAI News|https://openai.com/news/|ai|1|blog|daily|OpenAI GPT API modelli
chatgpt-notes|ChatGPT release notes|https://help.openai.com/en/articles/6825453-chatgpt-release-notes|ai|1|release_notes|daily|ChatGPT disponibilità funzioni
anthropic|Anthropic News|https://www.anthropic.com/news|ai|1|blog|daily|Claude modelli ricerca
qwen|Qwen Blog|https://qwen.ai/blog|ai|1|blog|rotating|Qwen modelli locali multimodali
ollama|Ollama Blog|https://ollama.com/blog|ai|1|blog|rotating|Ollama modelli locali
deepmind|Google DeepMind Blog|https://deepmind.google/blog/|ai|1|blog|rotating|Gemini modelli ricerca
mistral|Mistral News|https://mistral.ai/news/|ai|1|blog|rotating|Mistral modelli locali
lmstudio|LM Studio Blog|https://lmstudio.ai/blog|ai|1|blog|rotating|inferenza locale LM Studio
huggingface|Hugging Face Blog|https://huggingface.co/blog|ai|2|aggregator|on_gap|modelli open weights tool ricerca
localllama|r/LocalLLaMA|https://www.reddit.com/r/LocalLLaMA/|ai|3|community|optional|LLM locali inferenza quantizzazione
pi|Pi Agent releases|https://github.com/earendil-works/pi/releases|agents|1|release_notes|daily|Pi Agent estensioni provider
mcp|Model Context Protocol Blog|https://blog.modelcontextprotocol.io/|agents|1|blog|daily|MCP protocollo integrazioni
github-copilot|GitHub Copilot changelog|https://github.blog/changelog/label/copilot/|agents|1|release_notes|rotating|Copilot coding agent CLI IDE
vscode|Visual Studio Code updates|https://code.visualstudio.com/updates|agents|1|release_notes|rotating|IDE coding agent integrazioni
aider|Aider history|https://aider.chat/HISTORY.html|agents|1|release_notes|rotating|coding terminale agenti
cline|Cline Blog|https://cline.bot/blog|agents|1|blog|rotating|coding agent strumenti
cursor|Cursor changelog|https://cursor.com/changelog|agents|1|release_notes|rotating|coding agent IDE
showhn|Show Hacker News|https://news.ycombinator.com/show|agents|3|community|optional|scouting tool agenti developer
copilot-studio|Copilot Studio whats new|https://learn.microsoft.com/en-us/microsoft-copilot-studio/whats-new|work|1|release_notes|daily|Copilot Studio chatbot Knowledge Base
copilot-blog|Microsoft Copilot Blog|https://www.microsoft.com/en-us/copilot/blog/|work|1|blog|daily|Microsoft 365 Copilot Digital Workplace
m365-roadmap|Microsoft 365 Roadmap|https://www.microsoft.com/en-us/microsoft-365/roadmap|work|1|roadmap|rotating|Teams SharePoint Copilot roadmap
sharepoint|Microsoft SharePoint Blog|https://techcommunity.microsoft.com/category/content_management/blog/spblog|work|1|blog|rotating|SharePoint gestione documentale knowledge
teams|Microsoft Teams Blog|https://techcommunity.microsoft.com/category/microsoftteams/blog/microsoftteamsblog|work|1|blog|rotating|Teams Digital Workplace
entra|Microsoft Entra whats new|https://learn.microsoft.com/en-us/entra/fundamentals/whats-new|work|1|release_notes|rotating|Entra identità governance
azure-search|Azure AI Search whats new|https://learn.microsoft.com/en-us/azure/search/whats-new|work|1|release_notes|rotating|RAG enterprise search KB
practical365|Practical 365|https://practical365.com/|work|2|publication|on_gap|Microsoft 365 workplace amministrazione
unity|Unity Blog|https://unity.com/blog|gamedev|1|blog|daily|Unity Web mobile authoring asset
blender|Blender release notes|https://developer.blender.org/docs/release_notes/|gamedev|1|release_notes|rotating|Blender 3D rigging animazione
krita|Krita News|https://krita.org/en/posts/|gamedev|1|blog|rotating|Krita grafica 2D animazione
gimp|GIMP News|https://www.gimp.org/news/|gamedev|1|blog|rotating|GIMP editing asset 2D
odin|Odin Inspector patch notes|https://odininspector.com/patch-notes|gamedev|1|release_notes|rotating|Unity Odin authoring editor
80level|80 Level|https://80.lv/|gamedev|2|publication|on_gap|asset 2D 3D AI rigging tool game development
champions|Pokemon Champions official|https://champions.pokemon.com/en-us/|gaming|1|official_site|daily|Pokémon Champions regolamenti eventi
pocket|Pokemon TCG Pocket official|https://tcgpocket.pokemon.com/en-us/|gaming|1|official_site|daily|Pokémon TCG Pocket carte eventi
dokkan|Dokkan Battle Bandai Namco|https://dbz-dokkan.bn-ent.net/|gaming|1|official_site|daily|Dragon Ball Z Dokkan Battle Global JP
dokkan-news|Dragon Ball official Dokkan news|https://en.dragon-ball-official.com/search.php?tag=dokkanbattle|gaming|1|official_site|rotating|Dokkan Battle annunci distinguere merchandise
nintendo|Nintendo News|https://www.nintendo.com/us/whatsnew/|gaming|1|blog|rotating|Switch 2 Switch Direct showcase ecosistema
xbox|Xbox Wire|https://news.xbox.com/en-us/|gaming|1|blog|rotating|Xbox servizi RPG console showcase
steam|Steam News Hub|https://store.steampowered.com/news/|gaming|2|aggregator|on_gap|Steam demo roguelike RPG deckbuilder
gog|GOG Blog|https://www.gog.com/blog/|gaming|1|blog|rotating|retrogaming preservazione cataloghi
dolphin|Dolphin development blog|https://dolphin-emu.org/blog/|gaming|1|blog|rotating|emulazione preservazione retrocompatibilità
serebii|Serebii|https://www.serebii.net/|gaming|2|publication|on_gap|Champions Pocket verificare gioco specifico
gematsu|Gematsu|https://www.gematsu.com/|gaming|2|publication|on_gap|JRPG tactical fighting metroidvania soulslike
rpgsite|RPG Site|https://www.rpgsite.net/|gaming|2|publication|on_gap|RPG JRPG tattici build progressione
nintendolife|Nintendo Life|https://www.nintendolife.com/|gaming|2|publication|on_gap|Switch Nintendo Direct demo
timeextension|Time Extension|https://www.timeextension.com/|gaming|2|publication|on_gap|retrogaming remaster remake preservazione
dokkan-community|r/DBZDokkanBattle|https://www.reddit.com/r/DBZDokkanBattle/|gaming|3|community|optional|Dokkan Battle scouting eventi Global JP
windows|Windows Blog|https://blogs.windows.com/|devices|1|blog|daily|Windows firmware prestazioni Insider
nvidia|NVIDIA Blog|https://blogs.nvidia.com/|devices|1|blog|rotating|GPU NVIDIA driver prestazioni AI locale
android|Google Android Blog|https://blog.google/products-and-platforms/platforms/android/|devices|1|blog|rotating|Android funzioni aggiornamenti
samsung|Samsung Global Newsroom|https://news.samsung.com/global/|devices|1|blog|rotating|Samsung Galaxy S25 Ultra Android
steamdeck|Steam Deck updates|https://store.steampowered.com/news/app/1675200/|devices|1|release_notes|daily|Steam Deck SteamOS firmware
terramaster|TerraMaster Update Notice|https://forum.terra-master.com/en/viewforum.php?f=28|devices|1|official_forum|rotating|TerraMaster TOS NAS aggiornamenti
androidauthority|Android Authority|https://www.androidauthority.com/|devices|2|publication|on_gap|Android Samsung analisi dispositivi
gamingonlinux|GamingOnLinux|https://www.gamingonlinux.com/|devices|2|publication|on_gap|SteamOS Steam Deck compatibilità
deck-community|r/SteamDeck|https://www.reddit.com/r/SteamDeck/|devices|3|community|optional|Steam Deck compatibilità esperienza utenti'''
sources=[]
for row in rows.splitlines():
 id,name,url,cat,tier,typ,policy,topics=row.split('|');tier=int(tier)
 v={'id':id,'name':name,'url':url,'category':cat,'tier':tier,'role':{1:'primary',2:'discovery',3:'scouting'}[tier],'source_type':typ,'topics':[topics],'check_policy':policy,'requires_primary_verification':tier!=1,'enabled':True,'verified_on':'2026-09-27','verification_method':'web_content'}
 if id in ('qwen','steam','steamdeck'):v.update(verification_method='web_index',notes='Indice dinamico: verificare i singoli articoli; pagina vuota non significa assenza di novità.')
 if id=='blender':v.update(enabled=False,verification_method='pending_http',notes='Dominio ufficiale; lettura web bloccata. Abilitare dopo un recupero HTTP verificato; usare ricerca aperta nel frattempo.')
 if id=='huggingface':v['notes']='Piattaforma con autori diversi: il dominio non rende ogni contributo una fonte primaria.'
 if id=='terramaster':v['notes']='Primaria solo per annunci dello staff; commenti utenti sono testimonianze. Data del post originale, non ultimo commento.'
 if id=='m365-roadmap':v['notes']='Roadmap non equivale a disponibilità generale: verificare rollout e stato preview/GA.'
 if id=='dokkan':v['notes']='Sito giapponese; verificare Global/JP e fuso, non trasferire automaticamente eventi tra versioni.'
 sources.append(v)
queries={
'ai':['OpenAI ChatGPT API Codex release capabilities availability','Anthropic Claude model release availability','Qwen Ollama local LLM inference model release','Gemini Mistral local open models benchmark release'],
'agents':['Pi Agent release extensions provider support','MCP protocol servers integrations release','coding agents terminal IDE workflow tool release'],
'work':['Copilot Studio SharePoint knowledge base document processing release','Microsoft 365 Copilot Teams Digital Workplace roadmap release','Entra identity governance new features','RAG enterprise search retrieval document AI release'],
'gamedev':['Unity Web mobile performance authoring editor release','Odin Unity ScriptableObject prefab data driven tools release','Blender 3D rigging animation AI tool release','Krita GIMP 2D asset generation editing animation release'],
'gaming':['Pokemon Champions news regulation competition','Dragon Ball Z Dokkan Battle Global JP news events update','Pokemon TCG Pocket news update cards','JRPG tactical turn based strategy roguelike deckbuilder demo release','fighting metroidvania soulslike action RPG build demo release','Nintendo Switch 2 Xbox Steam showcase Direct services news','retrogaming preservation emulation remaster remake compatibility news','gaming industry distribution accessibility game design announcements'],
'devices':['Windows Android Samsung Galaxy S25 Ultra software firmware update','NVIDIA drivers GPU compatibility local AI performance','Steam Deck SteamOS Nintendo Switch 2 Xbox Series X firmware update','TerraMaster TOS NAS release update']}
write('config/SOURCES.json',{'version':2,'verified_on':'2026-09-27','notes':'Registro tecnico canonico. Fonti prioritarie, non whitelist. Query derivate dal profilo, non sostitutive delle preferenze personali. Verificare fatti, autori e date dei singoli articoli.','query_matrix':queries,'sources':sources})
p=ROOT/'config/pipeline.json';cfg=json.loads(p.read_text());cfg.update(version=2,main_target_min=10,main_target_max=16,radar_max=8,max_featured=3,discovery_candidate_target_min=30,discovery_candidate_target_max=50,main_window_hours=24,main_exceptional_lookback_hours=72,radar_lookback_days=7,rotating_per_category=2)
for key in ('default_window_hours','exceptional_lookback_hours','max_items'):cfg.pop(key,None)
write('config/pipeline.json',cfg)
p=ROOT/'docs/data/categories.json';d=json.loads(p.read_text());d['version']=2;d['note']='Configurazione UI. Le fonti e le query sono canoniche in config/SOURCES.json; le preferenze restano nel Second Brain.'
for n,c in enumerate(d['categories']):
 c.pop('topics',None);c.pop('discovery_sources',None);c['order']=n
write('docs/data/categories.json',d)
