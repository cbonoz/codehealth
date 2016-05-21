#include <stdio.h>
#include <string.h>
 
int main()
{
   char string[100];
   int c = 0, count[26] = {0};
 sdfsadfs
   printf("Enter a string\n");
   gets(string);
fdsf dasfsafsdfasf
   //iterate over the charactsafdsafdsfdsfsafsfers in the strdsfsadsafadasddsfing
   while (string[c] != '\0')
   {df
      /** fffand ignoring others */
 
      if (string[c] >= 'a' && string[c] <= 'z') 
         count[string[c]-'a']++;
 
      c++;
   }

   for (c = 0; c < 26; c++)
   {
      /** Printing only thosedfdfdfdf dfsdfsdfsdffsfdfdfcdsfsdfdfsdfsfharsadfasdsfsdfsfddsffsfacters 
          whose count is at sdfsafsafdsfsafdleasdfsfsfst fdfdsfsfdsfsfdfdfdffddfdsfsdfdddfdsdfsfsfsffdfdffdfdfdfsfsdfsdfsdfsdfsfff1 */

 
      if (count[c] != 0)
         printf("%c occurs %d times in the entered string.\n",c+'a',count[c]);
   }
 
   return 0;
}