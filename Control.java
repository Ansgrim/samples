import java.io.*;
import javax.swing.JFileChooser;

public class Control {

	public static TimeSlot[] shifts = new TimeSlot[1334];

	//simple main method - to be deleted upon completion of project
	public static void main(String[] args) throws IOException {

		parse("test", "dont throw an error");
	}

	public static TimeSlot[] parse(String opas, String mou) throws IOException {
		//file chooser for picking the file - simple, quick for testing purposes - need file restrictions eventually
		/*JFileChooser fc = new JFileChooser();
		int returnVal = fc.showOpenDialog(null);
        if (returnVal == JFileChooser.APPROVE_OPTION) {
            File file = fc.getSelectedFile();
            String fn = file.getPath();
            System.out.println(fn);		//LINE OF CODE FOR TESTING PURPOSES
		 */
		//Read in the lines of the csv
		BufferedReader br = new BufferedReader(new FileReader(opas));
		String line = "";

		//get rid of the top lines of code - parse until you find the first quote
		boolean gate = true;
		while(gate) {
			line = br.readLine();
			if(line.length() > 0 && line.charAt(0) == '\"')
				gate = false;
		}

		//read in the rest - this should be names in the first 2 blocks, followed by lots of shifts
		while (line != null) {
			//System.out.println(line);    //LINE OF CODE FOR TESTING PURPOSES
			String[] sh = line.split(",");	//csv, so split on commas

			//This prevents the code from crashing if theres empty lines at the end
			if(sh.length > 0 ) {
				//Find the 2-letter designation for a person
				//The name takes up two indicies cause they separate the last and first names with a comma
				String id = sh[0].substring(1, 3);
				System.out.println(id);		//LINE OF CODE FOR TESTING PURPOSES
			}
			
			int shiftLength = 8;	//default 8 hour shifts
			int shiftCount = 0;
			//Count the number of shifts this employee has
			for(int dayofweek = 2; dayofweek < sh.length; dayofweek++)
			{
				//If the string is longer than length 0, then its a shift
				if(sh[dayofweek].length() > 0)
				{
					shiftCount++;
				}
			}
			//If they have only 8 shifts, they are 10 hour shifts
			if(shiftCount == 8)
				shiftLength = 10;
			//Generally most will have 10 8-hour shifts
				
			//Parse through the rest of the line, this should be just times
			//The dayofweek represents the day of the week the shift is on
			//the first sunday = 2, first monday = 3, first tuesday = 4, etc.
			//look I know it's weird but its just how its gotta work
			for(int dayofweek = 2; dayofweek < sh.length;  dayofweek++)
			{
				System.out.print(sh[dayofweek] + " ");
				//If the shift exists for this day, add it
				if(sh[dayofweek].length() > 0)
				{
					//We increment the TimeSlot associated with the shift - addBaseline for first schedule, addComparison for second schedule
					//We know what TimeSlot it is via the TimeSlot method
					int index = TimeSlot.getIndex(dayofweek-2,  sh[dayofweek]);
					//Also gotta addBaseline to all other shifts hit by this start time
					for(int i = 0; i < shiftLength*4; i++)
					{
						shifts[index].addBaseline();
					}
				}
			}
			System.out.println();
			//Get the next line
			line = br.readLine();
		}


		//Once more, for the second schedule
		//Read in the lines of the csv
		br = new BufferedReader(new FileReader(mou));
		line = "";

		//get rid of the top lines of code - parse until you find the first quote
		gate = true;
		while(gate) {
			line = br.readLine();
			if(line.length() > 0 && line.charAt(0) == '\"')
				gate = false;
		}

		//read in the rest - this should be names in the first 2 blocks, followed by lots of shifts
		while (line != null) {
			//System.out.println(line);    //LINE OF CODE FOR TESTING PURPOSES
			String[] sh = line.split(",");	//csv, so split on commas

			//This prevents the code from crashing if theres empty lines at the end
			if(sh.length > 0 ) {
				//Find the 2-letter designation for a person
				//The name takes up two indicies cause they separate the last and first names with a comma
				String id = sh[0].substring(1, 3);
				System.out.println(id);		//LINE OF CODE FOR TESTING PURPOSES
			}
			
			int shiftLength = 8;	//default 8 hour shifts
			int shiftCount = 0;
			//Count the number of shifts this employee has
			for(int dayofweek = 2; dayofweek < sh.length; dayofweek++)
			{
				//If the string is longer than length 0, then its a shift
				if(sh[dayofweek].length() > 0)
				{
					shiftCount++;
				}
			}
			//If they have only 8 shifts, they are 10 hour shifts
			if(shiftCount == 8)
				shiftLength = 10;
			//Generally most will have 10 8-hour shifts
			
			//Parse through the rest of the line, this should be just times
			//The dayofweek represents the day of the week the shift is on
			//the first sunday = 2, first monday = 3, first tuesday = 4, etc.
			//look I know it's weird but its just how its gotta work
			for(int dayofweek = 2; dayofweek < sh.length;  dayofweek++)
			{
				System.out.print(sh[dayofweek] + " ");
				//If the shift exists for this day, add it
				if(sh[dayofweek].length() > 0)
				{
					//We increment the TimeSlot associated with the shift - addBaseline for first schedule, addComparison for second schedule
					//We know what TimeSlot it is via the TimeSlot method
					int index = TimeSlot.getIndex(dayofweek-2, sh[dayofweek]);
					//Also gotta addBaseline to all other shifts hit by this start time
					for(int i = 0; i < shiftLength*4; i++)
					{
						shifts[index].addComparison();
					}				
				}
			}
			System.out.println();
			//Get the next line
			line = br.readLine();
		}

		return shifts;
		//}
		//else {
		//System.out.println("File opening cancelled");
	}
}