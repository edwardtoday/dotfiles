FasdUAS 1.101.10   ��   ��    k             l     ��  ��    ) # Remove Duplicate Phone Numbers 1.1     � 	 	 F   R e m o v e   D u p l i c a t e   P h o n e   N u m b e r s   1 . 1   
  
 l     ��  ��    + % By Trevor Harmon <trevor@vocaro.com>     �   J   B y   T r e v o r   H a r m o n   < t r e v o r @ v o c a r o . c o m >      l     ��  ��    : 4 License: GPL - http://www.gnu.org/copyleft/gpl.html     �   h   L i c e n s e :   G P L   -   h t t p : / / w w w . g n u . o r g / c o p y l e f t / g p l . h t m l      l     ��������  ��  ��        l      ��  ��    � �
This script will walk through every *selected* contact in the Address Book and remove any duplicate phone numbers that it finds.
     �   
 T h i s   s c r i p t   w i l l   w a l k   t h r o u g h   e v e r y   * s e l e c t e d *   c o n t a c t   i n   t h e   A d d r e s s   B o o k   a n d   r e m o v e   a n y   d u p l i c a t e   p h o n e   n u m b e r s   t h a t   i t   f i n d s . 
      l     ��������  ��  ��        l    � ����  O     �   !   k    � " "  # $ # r     % & % m    ����   & o      ���� 0 
duplicates   $  ' ( ' r     ) * ) m    	����   * o      ���� 0 people_with_duplicates   (  + , + X    � -�� . - k    � / /  0 1 0 r    " 2 3 2 J     ����   3 o      ���� 0 unique_phones   1  4 5 4 r   # ' 6 7 6 J   # %����   7 o      ���� 0 duplicate_phones   5  8 9 8 X   ( d :�� ; : k   : _ < <  = > = r   : D ? @ ? n  : B A B A I   ; B�� C���� 0 numbersonly numbersOnly C  D�� D n   ; > E F E 1   < >��
�� 
az17 F o   ; <���� 0 
this_phone  ��  ��   B  f   : ; @ o      ���� 0 phone_value   >  G�� G Z   E _ H I�� J H E  E H K L K o   E F���� 0 unique_phones   L o   F G���� 0 phone_value   I k   K X M M  N O N r   K R P Q P b   K P R S R o   K L���� 0 duplicate_phones   S l  L O T���� T n   L O U V U 1   M O��
�� 
ID   V o   L M���� 0 
this_phone  ��  ��   Q o      ���� 0 duplicate_phones   O  W�� W r   S X X Y X [   S V Z [ Z o   S T���� 0 
duplicates   [ m   T U����  Y o      ���� 0 
duplicates  ��  ��   J s   [ _ \ ] \ o   [ \���� 0 phone_value   ] l      ^���� ^ n       _ ` _  ;   ] ^ ` o   \ ]���� 0 unique_phones  ��  ��  ��  �� 0 
this_phone   ; n   + . a b a 2   , .��
�� 
az20 b o   + ,���� 0 this_person   9  c d c X   e � e�� f e I  u ��� g��
�� .coredelonull���     obj  g l  u � h���� h 6  u � i j i n   u x k l k 2  v x��
�� 
az20 l o   u v���� 0 this_person   j =  y � m n m 1   z |��
�� 
ID   n o   } ���� 0 phone_id  ��  ��  ��  �� 0 phone_id   f o   h i���� 0 duplicate_phones   d  o�� o Z   � � p q���� p >  � � r s r o   � ����� 0 duplicate_phones   s J   � �����   q r   � � t u t [   � � v w v o   � ����� 0 people_with_duplicates   w m   � �����  u o      ���� 0 people_with_duplicates  ��  ��  ��  �� 0 this_person   . l    x���� x 2    ��
�� 
azf4��  ��   ,  y z y I  � �������
�� .coresavenull���     null��  ��   z  {�� { I  � ��� | }
�� .sysodlogaskr        TEXT | b   � � ~  ~ b   � � � � � b   � � � � � b   � � � � � m   � � � � � � �  R e m o v e d   � o   � ����� 0 
duplicates   � m   � � � � � � � "   d u p l i c a t e s   f r o m   � o   � ����� 0 people_with_duplicates    m   � � � � � � �    r e c o r d s . } �� ���
�� 
btns � J   � � � �  ��� � m   � � � � � � �  O K��  ��  ��   ! m      � ��                                                                                  adrb  alis    f  Macintosh HD               �<�H+     YAddress Book.app                                                9-�,\�        ����  	                Applications    �<q      �+�J       Y  +Macintosh HD:Applications: Address Book.app   "  A d d r e s s   B o o k . a p p    M a c i n t o s h   H D  Applications/Address Book.app   / ��  ��  ��     � � � l     ��������  ��  ��   �  ��� � i      � � � I      �� ����� 0 numbersonly numbersOnly �  ��� � o      ���� 0 pstring pString��  ��   � k     = � �  � � � r      � � � m      � � � � �   � o      ���� 0 	trtnvalue 	tRtnValue �  � � � r    	 � � � n     � � � 1    ��
�� 
ID   � o    ���� 0 pstring pString � o      ���� 0 tlist tList �  � � � X   
 : ��� � � Z    5 � ����� � F    % � � � l    ����� � ?     � � � o    ���� 0 tchar tChar � m    ���� /��  ��   � l    # ����� � A     # � � � o     !���� 0 tchar tChar � m   ! "���� :��  ��   � r   ( 1 � � � b   ( / � � � o   ( )���� 0 	trtnvalue 	tRtnValue � l  ) . ����� � 5   ) .�� ���
�� 
TEXT � o   + ,���� 0 tchar tChar
�� kfrmID  ��  ��   � o      ���� 0 	trtnvalue 	tRtnValue��  ��  �� 0 tchar tChar � o    ���� 0 tlist tList �  ��� � L   ; = � � o   ; <���� 0 	trtnvalue 	tRtnValue��  ��       �� � � ���   � ������ 0 numbersonly numbersOnly
�� .aevtoappnull  �   � **** � �� ����� � ����� 0 numbersonly numbersOnly�� �� ���  �  ���� 0 pstring pString��   � ���������� 0 pstring pString�� 0 	trtnvalue 	tRtnValue�� 0 tlist tList�� 0 tchar tChar � 
 �������~�}�|�{�z�y
�� 
ID  
�� 
kocl
� 
cobj
�~ .corecnte****       ****�} /�| :
�{ 
bool
�z 
TEXT
�y kfrmID  �� >�E�O��,E�O /�[��l kh ��	 ���& �*��0%E�Y h[OY��O� � �x ��w�v � ��u
�x .aevtoappnull  �   � **** � k     � � �  �t�t  �w  �v   � �s�r�q�s 0 this_person  �r 0 
this_phone  �q 0 phone_id   �  ��p�o�n�m�l�k�j�i�h�g�f�e�d ��c�b � � ��a ��`�p 0 
duplicates  �o 0 people_with_duplicates  
�n 
azf4
�m 
kocl
�l 
cobj
�k .corecnte****       ****�j 0 unique_phones  �i 0 duplicate_phones  
�h 
az20
�g 
az17�f 0 numbersonly numbersOnly�e 0 phone_value  
�d 
ID   �  
�c .coredelonull���     obj 
�b .coresavenull���     null
�a 
btns
�` .sysodlogaskr        TEXT�u �� �jE�OjE�O �*�-[��l kh  jvE�OjvE�O ;��-[��l kh )��,k+ E�O�� ȡ�,%E�O�kE�Y ��6G[OY��O $�[��l kh ��-�[�,\Z�81j [OY��O�jv 
�kE�Y h[OY�}O*j Oa �%a %�%a %a a kvl Uascr  ��ޭ