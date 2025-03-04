class StringNumber{
//Source CODE URL: https://sentry.io/answers/how-do-i-convert-a-string-to-an-int-in-java/#:~:text=The%20two%20easiest%20ways%20to,valueOf()%20.

    public static void main(String[] args) {







        
    }

//======================> String to Int
    public static int valueOfStringProcess(String value) {
       

        try {
            return Integer.valueOf(value);
          
        } catch (NumberFormatException e) {
            System.out.println("Invalid integer input");
            return null;
        }
    }
    

    public static int parseIntProcess(String value) {

        try {

            return Integer.parseInt(value);
           
        } catch (NumberFormatException e) {
            System.out.println("Invalid integer input");
            return null;
        }
    }



    public static void teste3() {
        String s1 = "1000";
        String s2 = "1000";
        Integer n1 = Integer.valueOf(s1);
        Integer n2 = Integer.valueOf(s2);
        System.out.println("n1 == n2: " + String.valueOf(n1 == n2));
    }


    public static void teste4() {
        String s1 = "100";
        String s2 = "100";
        Integer n1 = Integer.valueOf(s1);
        Integer n2 = Integer.valueOf(s2);
        System.out.println("n1 == n2: " + String.valueOf(n1 == n2));
    }

//======================> String to Float





//======================> String to Double





//======================> String to Long






//======================> String to Boolean 
}



