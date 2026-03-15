#include <iostream>
using namespace std;

int main(){

    int n;
    cin >> n;

    int sum = 0;

    for(int i = n; i >= 1; i--){
        sum = sum + i;
    }

    cout << sum << endl;

    return 0;
}
