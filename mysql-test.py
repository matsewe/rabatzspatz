import pymysql

def log(self, data):
    print(data)
    self.execute(data)

def main():
    # Open database connection host user password database
    db = pymysql.connect("localhost", "rabatzspatz", "spatznrabatz", "rabatzspatz" )

    pymysql.cursors.Cursor.loggedExec = log
    # prepare a cursor object using cursor() method
    cursor = db.cursor()

    # execute SQL query using execute() method.

    cursor.loggedExec("SELECT * FROM Persons WHERE ChatID=1")

    print(cursor.rownumber)
    # Fetch a single row using fetchone() method.
    data = cursor.fetchall()
    print (data)

    # disconnect from server
    db.close()

if __name__ == '__main__':
    main()