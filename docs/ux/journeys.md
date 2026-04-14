# User journey-k

## 1. Gyors hozzáférés a tutorhoz
Persona: Egy egyetemista hallgató, aki már rendelkezik fiókkal, és minél gyorsabban el akar jutni a matematikai chat munkaterületre.

Belépési pont: App indulás nyilvános állapotban, bejelentkezési oldal.

Lépések:
1. S01 - Bejelentkezés: a felhasználó megadja az email és jelszó mezőket, majd rákattint a Login gombra; a rendszer siker esetén tokent ment és a főoldalra irányít; hibaág: hibás adatok esetén Invalid credentials üzenet jelenik meg.
2. S03 - Főoldal: a felhasználó a betöltött chat felületet, mappalistát és mentett chat listát látja; a rendszer lekéri a mappákat és a chateket; hibaág: ha token hiányzik vagy auth hiba van, átirányítás történik S01-re.
3. S03 - Főoldal: a felhasználó ellenőrzi, hogy elérhető-e az Új chat indítása és a chatküldés; a rendszer interaktív tutor panelt mutat; hibaág: ideiglenes backend probléma esetén toast hibaüzenet jelenik meg.

Sikerkritérium: A felhasználó hitelesítve eljut az S03 képernyőre, és aktívan tud új chatet indítani vagy meglévő chatet megnyitni.

Mért időtartam (kb.): 20-40 mp, 3-5 kattintás.

## 2. Új matematikai chat indítása és folytatása
Persona: Egy gyakorló diák, aki új feladatot kér, majd ugyanabban a beszélgetésben követő kérdésekkel halad tovább.

Belépési pont: Hitelesített állapotban S03 - Főoldal.

Lépések:
1. S03 - Főoldal: a felhasználó az Új chat gombra kattint, majd beír egy matematikai kérést és elküldi; a rendszer a chats/start végponton létrehozza a beszélgetést és visszaadja az első tutor választ; hibaág: üres üzenetnél nincs beküldés, szolgáltatáshiba esetén hiba toast jelenik meg.
2. S03 - Főoldal: a felhasználó a létrejött chatet a jobb oldali panelen látja, és újabb üzenetet küld; a rendszer a chats/{chat_id}/messages végponton folytatja a beszélgetést és frissíti az üzenetlistát; hibaág: API hiba esetén a válasz nem frissül, hiba toast jelenik meg.
3. S03 - Főoldal: a felhasználó opcionálisan mappát hoz létre, majd a chatet mappához rendeli; a rendszer létrehozza a mappát és patch művelettel áthelyezi a chatet; hibaág: létrehozási vagy mozgatási hiba esetén sikertelen művelet toast jelenik meg.
4. S03 - Főoldal: a felhasználó később kiválasztja a mentett chatet a listából és folytatja; a rendszer betölti a teljes chat részleteit és üzeneteit; hibaág: nem létező vagy nem elérhető chat esetén chat betöltési hibaüzenet jelenik meg.

Sikerkritérium: A felhasználó legalább egy új beszélgetést létrehoz, tutor választ kap, majd ugyanazt a chatet később is meg tudja nyitni és folytatni.

Mért időtartam (kb.): 60-150 mp, 6-12 kattintás.

## 3. Fiókkezelés a profilban (jelszócsere vagy törlés)
Persona: Egy biztonságtudatos felhasználó, aki karbantartja a fiókját, jelszót cserél vagy megszünteti a hozzáférését.

Belépési pont: Hitelesített navigációból S04 - Profil.

Lépések:
1. S03 - Főoldal: a felhasználó a felső navigációban a Profile linkre kattint; a rendszer profil oldalra vált és lekéri az emailt, valamint a mentett chat listát; hibaág: token hiány vagy auth hiba esetén átirányítás S01-re.
2. S04 - Profil: a felhasználó a Change password gombra kattint; a rendszer megnyitja a modális jelszócsere ablakot; hibaág: ha a profiladatok nem tölthetők, az oldal visszairányíthat S01-re.
3. S06 - Jelszó módosítása: a felhasználó megadja a régi és új jelszót, majd Save; a rendszer validál és siker esetén bezárja a modalt; hibaág: üres mezők, azonos régi-új jelszó, hibás régi jelszó vagy backend hiba esetén hiba toast jelenik meg.
4. S04 - Profil: alternatív ágban a felhasználó a Delete account gombra kattint és megerősíti a törlést; a rendszer törli a fiókot, törli a tokent és a regisztrációs oldalra irányít; hibaág: sikertelen törlés esetén a felhasználó a profilon marad hiba toasttal.
5. S04 vagy S03 - Kijelentkezés: a felhasználó Logout gombra kattint; a rendszer törli a tokent és S01-re navigál; hibaág: nincs külön hibaág, kliens oldali token törlés történik.

Sikerkritérium: A felhasználó sikeresen jelszót módosít, vagy sikeresen törli a fiókját, illetve bármikor biztonságosan ki tud jelentkezni.

Mért időtartam (kb.):
- Jelszócsere ág: 30-70 mp, 4-7 kattintás.
- Fióktörlés ág: 20-45 mp, 3-5 kattintás.