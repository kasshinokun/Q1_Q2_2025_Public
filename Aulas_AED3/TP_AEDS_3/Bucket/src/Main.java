public class Main {
	
	
	public static void main(String[] args) {
		writerArchive pager=new writerArchive("csv/random_people.csv","csv/persons.db");
		pager.writeAllFile();
	}

}
