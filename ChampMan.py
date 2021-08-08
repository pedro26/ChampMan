import datetime
import os
import platform
import re
import sqlite3
import time

_os = platform.system()


def clear():
    if _os == "Windows":
        os.system("cls")
    elif "linux" in _os:
        os.system("clear")
    else:
        print("Get a decent OS...")


def create_sql(conn):
    cur = conn.cursor()
    cur.execute("CREATE TABLE STATUS(STATUS INTEGER PRIMARY KEY);")
    cur.execute("""
        CREATE TABLE TEAMS(
            CODE VARCHAR(3) PRIMARY KEY,
            NAME VARCHAR(25)
        );
    """)
    cur.execute("""
        CREATE TABLE RANKING(
            CODE VARCHAR(3) PRIMARY KEY,
            W INTEGER,
            D INTEGER,
            L INTEGER,
            GF INTEGER,
            GA INTEGER
        );
    """)
    cur.execute("""
        CREATE TABLE MATCHES(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ROUND INT,
            TEAM1 VARCHAR(3),
            SCORE1 INTEGER,
            TEAM2 VARCHAR(3),
            SCORE2 INTEGER,
            MATCHDATE DATE
        );
    """)
    cur.execute("INSERT INTO STATUS VALUES(1);")


def list_teams(conn, wait):
    clear()
    print("<--- Team List --->\n")
    cur = conn.cursor()
    cur.execute("SELECT * FROM TEAMS")
    teams = cur.fetchall()
    for t in teams:
        print(f"{t[0]} - {t[1]}")
    print("")
    if wait:
        input("Press enter key to continue...")


def add_teams(conn):
    cur = conn.cursor()
    cur.execute("SELECT STATUS FROM STATUS")
    status = cur.fetchone()
    if int(status[0]) == 1:
        opt = "Y"
    else:
        print("This championship is ongoing or closed and you can't add more teams!")
        opt = "N"
    while opt != "N":
        if opt == "Y":
            clear()
            list_teams(conn, False)
            code = input("Insert the team code (3 characters): ")
            name = input("Insert the team name: ")
            if len(code) > 3:
                code = code[0:3]
            if len(name) > 25:
                name = name[0:25]
            try:
                cur.execute("INSERT INTO TEAMS VALUES(?, ?)", (code, name))
            except sqlite3.IntegrityError as error:
                print(f"Error including {code} - {name}!\n" + str(error))
            else:
                conn.commit()
                print("Team included with success!")
        opt = input("\nDo you want to continue including teams? (Y/N): ").upper()


def create():
    clear()
    print("<--- Championship Creation --->\n")
    name = re.sub("[^a-zA-Z0-9 \n]", "", input("Enter the name of the championship: "))
    if len(name) > 0:
        champ_list = os.listdir(".")
        if name + ".chp" not in champ_list:
            conn = sqlite3.connect(name + ".chp")
            create_sql(conn)
            conn.commit()
            print(f"Championship {name} created with success!\n")
            opt = ""
            while opt != "N":
                opt = input("Do you want to add teams now? (Y/N): ").upper()
                if opt == "Y":
                    add_teams(conn)
                    opt = "N"
                elif opt == "N":
                    break
                else:
                    opt = ""
            conn.close()
        else:
            print("Championship already exists!")
            time.sleep(2)
    else:
        print("The name of the championship can't be empty!")
        time.sleep(2)


def list_champs(operation):
    ret = ""
    clear()
    print(f"<--- Championship selection - {operation} --->\n")
    files = os.listdir(".")
    champs = []
    for f in files:
        if f.endswith(".chp"):
            champs.append(f)
    if len(champs) > 0:
        for c in champs:
            print(f"{champs.index(c) + 1} - {c.replace('.chp', '')}")
        chp = 0
        while chp == 0:
            try:
                chp = int(input("\nSelect the championship number: "))
            except ValueError:
                print("Invalid selection!")
                chp = 0
            else:
                if chp <= len(champs):
                    ret = champs[chp - 1]
    else:
        print("You don't have any championship created yet!")
        ret = ""
        time.sleep(2)
    return ret


def delete():
    champ = list_champs("Delete")
    if len(champ) == 0:
        pass
    elif os.path.exists(champ):
        os.remove(champ)
        print(f"{champ.replace('.chp', '')} deleted with success!")
    else:
        print(f"The championship {champ} could not be deleted!")
        time.sleep(2)


def del_teams(conn):
    cur = conn.cursor()
    opt = "Y"
    while opt != "N":
        if opt == "Y":
            list_teams(conn, False)
            team = input("Insert the team code to be deleted: ")
            cur.execute("DELETE FROM TEAMS WHERE CODE = ?", (team,))
            if cur.rowcount > 0:
                conn.commit()
                print(f"{team} deleted with success!")
            else:
                print(f"Could not possible find {team} in the database!")
        opt = input("\nDo you want to delete more teams? (Y/N): ").upper()


def get_rounds(teams):
    if len(teams) % 2:
        teams.append('---')
    n = len(teams)
    rounds = []
    for r in range(len(teams) - 1):
        l = list(teams[0:n])
        r %= (n - 1)
        if r:
            l = l[:1] + l[-r:] + l[1:-r]
        h = n // 2
        rounds.append(list(zip(l[:h], l[h:][::-1])))
    return rounds


def gen_matches(conn, home_away):
    cur = conn.cursor()
    cur.execute("SELECT CODE FROM TEAMS")
    codes = cur.fetchall()
    teams = []
    for c in codes:
        teams.append(c[0])
    rounds = get_rounds(teams)
    rn = 1
    for r in rounds:
        for match in r:
            if match[0] != "---" and match[1] != "---":
                cur.execute("INSERT INTO MATCHES(ROUND, TEAM1, TEAM2) VALUES(?, ?, ?)", (rn, match[0], match[1]))
        rn += 1
    conn.commit()
    cur.execute("UPDATE MATCHES SET TEAM1 = TEAM2, TEAM2 = TEAM1 WHERE (ROUND > 2 AND ROUND % 2 > 0)")
    if home_away:
        cur.execute("SELECT ROUND, TEAM2, TEAM1 FROM MATCHES")
        matches = cur.fetchall()
        ra = 1
        for m in matches:
            if m[0] != ra:
                ra = m[0]
                rn += 1
            team1 = m[1]
            team2 = m[2]
            cur.execute("INSERT INTO MATCHES(ROUND, TEAM1, TEAM2) VALUES(?, ?, ?)", (rn, team1, team2))
        conn.commit()
    for t in teams:
        cur.execute("INSERT INTO RANKING VALUES(?, ?, ? ,? ,?, ?)", (t, 0, 0, 0, 0, 0))
    conn.commit()


def change_stat(conn, champ, s_status):
    cur = conn.cursor()
    opt = 99
    while opt not in [0, 1, 2, 3]:
        clear()
        print(f"<--- Change Championship Status - {champ} --->\n")
        print(f"Current Status: {s_status}\n")
        print("1 - Not Started (this will clean all matches and stats!)")
        print("2 - Ongoing (this allows you to add match results)")
        print("3 - Closed (this will put the championship in view-only mode)")
        print("\n0 - Back")
        try:
            opt = int(input("\nSelect option: "))
        except ValueError:
            opt = 99
        if opt in [1, 2, 3]:
            cur.execute("UPDATE STATUS SET STATUS = ?", (opt,))
            conn.commit()
            print("\nStatus changed with success!")
            if opt == 1:
                print("\nCleaning matches and ranking...")
                cur.execute("DELETE FROM MATCHES")
                cur.execute("DELETE FROM RANKING")
                cur.execute("DELETE FROM SQLITE_SEQUENCE WHERE NAME = 'MATCHES'")
                conn.commit()
                print("Cleaned with success!")
            elif opt == 2 and s_status == "Not started":
                print("Generating matches...")
                opt2 = ""
                while opt2 not in ["Y", "N"]:
                    opt2 = input("Generate away matches? (Y/N): ").upper()
                home_away = False
                if opt2 == "Y":
                    home_away = True
                gen_matches(conn, home_away)
                print("Matches generated with success!")
            time.sleep(2)


def list_matches(conn, champ, selection):
    cur = conn.cursor()
    cur.execute("""
        SELECT 
        ID,
        ROUND,
        TEAM1,
        IFNULL(SCORE1, ' ') AS SCORE1,
        TEAM2,
        IFNULL(SCORE2, ' ') AS SCORE2,
        IFNULL(MATCHDATE, ' ') AS MATCHDATE
        FROM MATCHES
    """)
    matches = cur.fetchall()
    if not selection:
        clear()
        print(f"<--- Match list - {champ.replace('.chp', '')}--->")
    r = 0
    n = 0
    for m in matches:
        n += 1
        if r != m[1]:
            r = m[1]
            print(f"\n---- Round {r} ----")
        line = f"{str(m[0]).ljust(3)} - {m[2].ljust(4)}{str(m[3]).rjust(3)} "
        line += f"x {str(m[5]).ljust(4)}{m[4].ljust(3)} {m[6]}"
        print(line)
    opt = -1
    if selection:
        while opt != 0:
            i = input("\nSelect the match number (0 to cancel) or press N to select the next match: ")
            if i.upper() == "N":
                return -2
            else:
                try:
                    opt = int(i)
                except ValueError:
                    opt = -1
            if opt > n or opt == -1:
                print("Invalid match!")
                opt = -1
            else:
                break
        return opt
    else:
        input("\nPress enter key to continue...")


def ranking(conn, champ):
    clear()
    cur = conn.cursor()
    cur.execute("""SELECT NAME, (W*3)+(D*1) AS P, W+D+L AS PLD, W, D, L, GF, GA, GF-GA AS GD
                   FROM RANKING INNER JOIN TEAMS ON RANKING.CODE = TEAMS.CODE
                   ORDER BY 2 DESC, 4 DESC, 9 DESC, 7 DESC, 3""")
    rank = cur.fetchall()
    print(f"<--- {champ.replace('.chp', '')} --->\n")
    print("   Team                      P  PLD W  D  L  GF GA GD")
    c = 1
    for team in rank:
        line = f"{str(c).ljust(3)}{team[0].ljust(26)}{str(team[1]).ljust(3)}{str(team[2]).ljust(4)}"
        line += f"{str(team[3]).ljust(3)}{str(team[4]).ljust(3)}{str(team[5]).ljust(3)}"
        line += f"{str(team[6]).ljust(3)}{str(team[7]).ljust(3)}{str(team[8]).ljust(3)}"
        print(line)
        c += 1
    input("\nPress enter key to continue...")


def update_rank(conn):
    cur = conn.cursor()
    cur.execute("UPDATE RANKING SET W = 0, D = 0, L = 0, GF = 0, GA = 0")
    conn.commit()
    cur.execute("SELECT * FROM MATCHES WHERE SCORE1 IS NOT NULL AND SCORE2 IS NOT NULL")
    matches = cur.fetchall()
    for m in matches:
        t1 = [0, 0, 0, 0, 0]
        t2 = [0, 0, 0, 0, 0]
        if m[3] > m[5]:
            t1[0] = 1
            t2[2] = 1
        elif m[3] == m[5]:
            t1[1] = 1
            t2[1] = 1
        else:
            t1[2] = 1
            t2[0] = 1
        t1[3] = m[3]
        t2[4] = m[3]
        t1[4] = m[5]
        t2[3] = m[5]
        cur.execute("UPDATE RANKING SET W = W + ?, D = D + ?, L = L + ?, GF = GF + ?, GA = GA + ? WHERE CODE = ?",
                    (t1[0], t1[1], t1[2], t1[3], t1[4], m[2]))
        cur.execute("UPDATE RANKING SET W = W + ?, D = D + ?, L = L + ?, GF = GF + ?, GA = GA + ? WHERE CODE = ?",
                    (t2[0], t2[1], t2[2], t2[3], t2[4], m[4]))
    conn.commit()


def results(conn, champ):
    dt = None
    opt = "Y"
    while opt == "Y":
        clear()
        print(f"<--- {champ.replace('.chp', '')} - Match Results --->\n")
        match = list_matches(conn, champ, True)
        if match != 0:
            cur = conn.cursor()
            if match == -2:
                cur.execute("SELECT * FROM MATCHES WHERE SCORE1 IS NULL AND SCORE2 ISNULL ORDER BY ID LIMIT 1")
            else:
                cur.execute("SELECT * FROM MATCHES WHERE ID = ?", (match,))
            teams = cur.fetchone()
            if teams is not None:
                print(f"\n{teams[2]} x {teams[4]}")
                try:
                    score1 = int(input(f"{teams[2]}: "))
                    score2 = int(input(f"{teams[4]}: "))
                    i_dt = input("Date (YYYY-MM-DD or T for today): ")
                    if i_dt.upper() == "T":
                        dt = datetime.date.today()
                    else:
                        y, m, d = map(int, i_dt.split('-'))
                        dt = datetime.date(y, m, d)
                except ValueError:
                    score1 = score2 = -1
                if score1 < 0 or score2 < 0:
                    print("Invalid scores or date!")
                else:
                    cur.execute("UPDATE MATCHES SET SCORE1 = ?, SCORE2 = ?, MATCHDATE = ? WHERE ID = ?",
                                (score1, score2, dt, teams[0]))
                    conn.commit()
                    print("Score updated with success!")
                    update_rank(conn)
                    print("Ranking updated with success!")
                opt = ""
                print("")
                while opt not in ["Y", "N"]:
                    opt = input("Continue inserting results? (Y/N): ").upper()
            else:
                print("You have no matches without results!")
                time.sleep(2)
                opt = "Y"
        else:
            opt = "N"


def manage_champ(champ):
    conn = sqlite3.connect(champ)
    cur = conn.cursor()
    opt = 99
    while opt:
        clear()
        cur.execute("SELECT STATUS FROM STATUS")
        status = int(cur.fetchone()[0])
        if status == 1:
            s_status = "Not started"
        elif status == 2:
            s_status = "Ongoing"
        elif status == 3:
            s_status = "Closed"
        else:
            s_status = ""
        print(f"<--- {champ.replace('.chp', '')} - {s_status} --->\n")
        if status == 1:
            print("1 - Add new teams")
        print("2 - List teams")
        if status == 1:
            print("3 - Delete a team")
        print("4 - Change championship status")
        if status in [2, 3]:
            print("5 - List matches")
        if status == 2:
            print("6 - Insert match results")
        if status in [2, 3]:
            print("7 - Show current ranking")
        print("\n0 - Back")
        try:
            opt = int(input("\nSelect option: "))
        except ValueError:
            opt = 99
        if opt == 1 and status == 1:
            add_teams(conn)
        elif opt == 2:
            list_teams(conn, True)
        elif opt == 3 and status == 1:
            del_teams(conn)
        elif opt == 4:
            change_stat(conn, champ, s_status)
        elif opt == 5 and status in [2, 3]:
            list_matches(conn, champ, False)
        elif opt == 6 and status == 2:
            results(conn, champ)
        elif opt == 7 and status in [2, 3]:
            ranking(conn, champ)
    conn.close()


def manage():
    champ = list_champs("Manage")
    if len(champ) > 0:
        manage_champ(champ)


def my_credits():
    clear()
    print("ChampMan - Copyleft 2021")
    print("\nCreated by Pedro Augusto Domingues")
    print("\nContact: pedroaugusto2612@gmail.com")
    input("\nPress enter key to return...")


def menu():
    print("<--- Options --->\n")
    print("1 - Manage a Championship")
    print("2 - Create a new Championship")
    print("3 - Delete a Championship\n")
    print("9 - Credits\n")
    print("0 - Exit\n")
    try:
        opt = int(input("Select option: "))
    except ValueError:
        opt = 99
    if opt == 1:
        manage()
    elif opt == 2:
        create()
    elif opt == 3:
        delete()
    elif opt == 9:
        my_credits()
    return opt


if __name__ == "__main__":
    clear()
    while menu():
        clear()
    clear()
