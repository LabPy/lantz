#include<stdio.h>
#include<stdlib.h>

int returni10()
{
  return 10;
}

float returnf10()
{
  return (float) 10.;
}

double returnd10()
{
  return (double) 10.;
}

int sumi13(int x)
{
  return x + 13;
}

int use_atoi(const char * here, const int maxlen) {
  return atoi(here);
}

int write_in_charp(char * here, const int maxlen) {
  char * there = "28G11AC10T32";
  int i;
  for (i=0; i < maxlen; ++i) {
      *(here + i) = *(there + i);
  }
  return 1;
}

int double_param (double *p) {
   *p = 7;
   return 1;
}

int double_array_param(double * pdValarray) {
 pdValarray[0] = 1;
 pdValarray[1] = 2;
 pdValarray[2] = 3;
 return 1;
}

int double_array_length_param(double * pdValarray, const int maxlen) {
 int i;
 for (i=0; i<maxlen; i++) {
     pdValarray[i] = i;
 }
 return 1;
}

double sum_double_array(double * pdValarray) {
 return pdValarray[0] + pdValarray[1] + pdValarray[2];
}

double sum_double_array_length(double * pdValarray, const int maxlen) {
 double sum = 0;
 int i;
 for (i=0; i<maxlen; i++) {
     sum += pdValarray[i];
 }
 return sum;
}

