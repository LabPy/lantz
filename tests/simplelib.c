#include<stdio.h>
#include<stdlib.h>

int returni10()
{
  return 10;
}

int sumi13(int x)
{
  return x + 13;
}

float returnf10()
{
  return (float) 10.;
}

double returnd10()
{
  return (double) 10.;
}

int withCharp(char * here, const int maxlen) {
  char * there = "28G11AC10T32";
  int i;
  for (i=0; i < maxlen; ++i) {
      *(here + i) = *(there + i);
  }
  return 0;
}

int atoime(const char * here, const int maxlen) {
  return atoi(here);
}

int double_param(double * pdValarray) {
 pdValarray[0] = 1;
 pdValarray[1] = 2;
 pdValarray[2] = 3;
 return 0;
}

int change (int *p) {
   *p = 7;
   return 1;
}
int really_change (int **pp) {
   *pp = 7;
   return 1;
}

