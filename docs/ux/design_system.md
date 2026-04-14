# Design rendszer / vizuális nyelv

## 1. UI könyvtár / komponens-könyvtár
- A felület alapja Next.js + React + Tailwind CSS.
- A projektben főként egyedi, projekt-specifikus komponensek vannak utility class alapú stílusozással (pl. navigáció, chat felület, profil, űrlapok, modal).
- Visszajelzésekhez react-hot-toast használat történik.
- A csomaglistában szerepel Headless UI és Heroicons, de a jelenlegi implementált képernyőkben nem látható aktív használatuk.
- Nincs bevezetett külön UI design library (pl. MUI, shadcn/ui, Bootstrap) a ténylegesen renderelt felületeken.

## 2. Színpaletta
A színek Tailwind utility osztályokból vezethetők le. Az alábbi értékek a Tailwind alap palettájának megfelelő, kódból jól inferálható hex kódok:

- primary: Indigo 600 (#4F46E5) - fő CTA gombok, link hangsúlyok.
- secondary: Slate 700 (#334155) - másodlagos szöveg és navigációs címkék.
- accent: Emerald 700 (#047857) - tutor badge kiemelés.
- success: Emerald 700 (#047857) - sikeres státuszjelölések és hangsúlyok.
- warning: hozzávetőleges Amber 500 (#F59E0B) - explicit warning token jelenleg nincs külön definiálva a kódban.
- error: Rose 600 (#E11D48) - hibaüzenetek, törlés, retry hibakezelés.
- surface: White (#FFFFFF), háttér Surface Slate 50 (#F8FAFC), kontúr Slate 200 (#E2E8F0).
- text: elsődleges Slate 900 (#0F172A), másodlagos Slate 600 (#475569), segédszöveg Slate 500 (#64748B).

Megjegyzés: A warning kategória a jelenlegi UI-ban nem külön tokenként jelenik meg, ezért ez óvatos becslés.

## 3. Tipográfia
- Egyedi betűtípus nincs bekötve; a rendszer Tailwind alap sans-serif stackre támaszkodik.
- Méretskála a felületen: text-xs, text-sm, text-lg, text-xl, text-2xl.
- Tipikus súlyok:
- Címsorok: font-semibold.
- Mezőcímkék: font-semibold.
- Gombok: jellemzően font-semibold.
- Törzsszöveg: normál súly, többnyire text-sm vagy alapértelmezett méret.

## 4. Spacing / grid
- A spacing logika Tailwind alapú, 4 px-es léptékre épül (pl. p-4 = 16 px, px-3 = 12 px, gap-5 = 20 px).
- Fő tartalom konténer: max-w-5xl (kb. 1024 px), középre igazítva.
- Auth oldalak: középre rendezett kártya, max-w-md (kb. 448 px).
- Fő chat képernyő: mobilon egy oszlop, nagyobb nézeten két oszlopos rács (bal oldali sidebar + fő chat panel).
- Modal minta: fix, teljes képernyős overlay, középre igazított max-w-md panel.

## 5. Ikonkészlet
- A jelenlegi implementációban a vizuális kommunikáció döntően szöveges címkékre, gombokra és natív űrlapelemekre épül.
- Aktív, következetesen használt ikonkészlet a renderelt UI-ban nem azonosítható.
- Heroicons függőség jelen van, de tényleges komponens import a vizsgált felületeken nem található.

## 6. Sötét mód
- Sötét mód jelenleg nem támogatott.
- Nem találhatók dark: előtagú utility osztályok, téma-váltó logika vagy külön dark tokenek.

## 7. Reszponzív breakpoint-ok
- Tailwind alap breakpoint rendszer érvényes (egyedi felülírás nincs a konfigurációban):
- sm: 640 px
- md: 768 px
- lg: 1024 px
- xl: 1280 px
- 2xl: 1536 px
- A ténylegesen használt reszponzív váltás főként lg szinten jelenik meg:
- A főoldali layout 1 oszlopról 2 oszlopra vált.
- Egyes oldalsáv elemek mobilon teljes szélességűek, asztali nézetben fixebb szélességet kapnak.

## 8. Forrás
- Külön design source (Figma, Penpot, dedikált token repository vagy theme fájl) nem található a projektben.
- A design rendszer elsődleges forrása a megvalósított frontend kód (Tailwind osztályok, layout komponensek, oldalak).
- A docs/ux/screenshots mappa képernyőképei a megvalósított vizuális állapotot alátámasztják, de a specifikáció alapja a kód.