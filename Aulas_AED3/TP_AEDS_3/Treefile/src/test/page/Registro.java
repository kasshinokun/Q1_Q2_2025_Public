package test.page;
public class Registro {
		int key;
		byte validation;
		long address;
		public Registro() {
			this.key=0;
			this.validation=0;
			this.address=-1;	
		}
		public Registro(int key,byte validation,long address) {
			
			this.key = key;
			this.validation = validation;
			this.address = address;
			
		}
		public void setKey(int key) {
			this.key = key;
		}
		public void setValidation(byte validation) {
			this.validation = validation;
		}
		public void setAddress(long address) {
			this.address = address;
		}
		public int getKey() {
			return this.key;
		}
		public boolean isValidation() {
			return validation==1?true:false;
		}
		public long getAddress() {
			return address;
		}
		String printRegistry() {
			return "ID do registro:---------> "+getKey()+
					"\nPosição do indice:------> "+getAddress()+
					"\nValidade:---------------> "+isValidation();
		}
	}